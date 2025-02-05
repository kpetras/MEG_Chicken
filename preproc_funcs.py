# preproc_funcs.py
# functions used for preprocessing
"""
Long explanation:
The preprocess_and_make_trials functions does the following:
1. Prepare the dataset structure to fit the set convention
data/
├── raw/                        
│   └── *.fif                     # Original raw data files (in FIF format) that remain unaltered 
├── dataset1/                   
│   ├── core_data/              
│   │   ├── preprocessed_channels/  
│   │   │   └── subj_ses_run/     # (No longer used in this version, but retained if needed.)
│   │   └── index_db/            
│   │       └── channel_index.db  
│   ├── ica/                    
│   │   └── {channel_type}/       
│   │       └── *.fif              
│   └── trials/                   # SQLite database storing trial information


2. Preprocessing the raw data if indicated
3. **Now forced to save the entire preprocessed data as a single *.fif file** inside core_data
4. ICA (optional)
5. Make trials file (optional)
"""
import os
import mne
import json
import random
import pickle
import sqlite3
import numpy as np
from tqdm import tqdm
import config

# -------------------------------
#           Core Dataset
# -------------------------------
def _init_core_storage(dataset_dir):
    """
    Initialize core_data structure:
    - core_data/preprocessed_channels/ : (Retained if needed for other tasks, but not used here)
    - core_data/index_db/ : store trial and channel index
    """
    core_path = os.path.join(dataset_dir, "core_data")
    # preprocessed_channels_dir = os.path.join(core_path, "preprocessed_channels")
    # os.makedirs(preprocessed_channels_dir, exist_ok=True)
    index_dir = os.path.join(core_path, "index_db")
    os.makedirs(index_dir, exist_ok=True)
    return core_path

def _save_dataset_config(core_path, dataset_config):
    config_file = os.path.join(core_path, "dataset_config.json")
    with open(config_file, 'w') as f:
        json.dump(dataset_config, f, indent=2)
    print(f"[DATASET CONFIG] Configuration saved at: {config_file}")

# ------------------------------------------
#   Saving the Entire Preprocessed Raw .fif
# ------------------------------------------
def _save_preprocessed_raw_fif(raw, core_path, subj, ses, run):
    """
    Name change: original_fname = "subj_ses_run.fif" -> "subj_ses_run_preproc_raw.fif"
    """
    preproc_name = f"{subj}_{ses}_{run}_preproc_raw.fif"
    save_path = os.path.join(core_path, preproc_name)
    raw.save(save_path, overwrite=True)
    print(f"[SAVED PREPROCESSED] {save_path}")


# --------------------------------------------
#               Trial DB
# --------------------------------------------
def _init_trial_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS trials (
        trial_id TEXT PRIMARY KEY,
        subj TEXT NOT NULL,
        ses TEXT NOT NULL, 
        run TEXT NOT NULL,
        ch_type TEXT CHECK(ch_type IN ('eeg','mag','grad')),
        version INTEGER,
        chs2display BLOB NOT NULL,
        bad_channels BLOB NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    
    conn.execute("""
    CREATE INDEX IF NOT EXISTS idx_trials_subj 
    ON trials (subj, ses, run)
    """)
    
    conn.commit()
    conn.close()

# -------------------------------
#           ICA
# -------------------------------
def _fit_and_save_ica(
    raw,
    ica_save_path, 
    ica_name,
    channel_type,
    n_components=config.ica_components, 
    method=config.ica_method, 
    random_state=config.ica_seed
):
    ica = mne.preprocessing.ICA(
        n_components=n_components, 
        method=method, 
        random_state=random_state
    )
    ica.fit(raw, picks=channel_type)
    ica_ch_save_path = os.path.join(ica_save_path, channel_type)
    os.makedirs(ica_ch_save_path, exist_ok=True)
    ica.save(os.path.join(ica_ch_save_path, ica_name), overwrite=True)
    print(f"[ICA] {channel_type} saved to {os.path.join(ica_ch_save_path, ica_name)}")


# -------------------------------
#     SELECT AND SHUFFLE 
# -------------------------------
def _select_and_shuffle_channels(
    raw, 
    bad_channels, 
    channel_type, 
    total_channels=15, 
    max_bad_channels=3, 
    min_bad_channels=1
):
    all_channels = raw.ch_names
    
    # Filter channels by type
    if channel_type == 'eeg':
        type_channels = [ch for ch in all_channels if ch.startswith('EEG')]
    elif channel_type == 'mag':
        type_channels = [ch for ch in all_channels if ch.startswith('MEG') and ch.endswith('1')]
    elif channel_type == 'grad':
        type_channels = [ch for ch in all_channels if ch.startswith('MEG') and ch.endswith(('2', '3'))]
    else:
        type_channels = []
    
    # Separate good/bad
    good_channels = [ch for ch in type_channels if ch not in bad_channels]
    bad_channels_in_type = [ch for ch in bad_channels if ch in type_channels]
    
    # Return None, None if we don't have enough bad channels to satisfy min_bad_channels
    if len(bad_channels_in_type) < min_bad_channels:
        return None, None
    
    # Randomly select bad channels
    num_bad = min(random.randint(min_bad_channels, max_bad_channels), len(bad_channels_in_type))
    selected_bad_channels = random.sample(bad_channels_in_type, num_bad) if num_bad > 0 else []

    # Randomly select good channels
    num_good = total_channels - num_bad
    selected_good_channels = random.sample(good_channels, min(num_good, len(good_channels)))

    # Combine and shuffle
    selected_channels = selected_good_channels + selected_bad_channels
    random.shuffle(selected_channels)

    return selected_channels, selected_bad_channels

# -------------------------------
#             Tools
# -------------------------------
def get_unique_path(dir, base_name="trials.db"):
    path = os.path.join(dir, base_name)
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(base_name)
    suffix = 1
    while True:
        new_name = f"{base}_{suffix}{ext}"
        new_path = os.path.join(dir, new_name)
        if not os.path.exists(new_path):
            return new_path
        suffix += 1


# -------------------------------
# PREPROCESS + MAKE TRIALS + ICA
# -------------------------------
def preprocess_and_make_trials(
    raw_dir,  # always "data/raw" 
    dataset_dir,  # e.g. "data/datasetName/"
    channel_types,
    l_freq=0.1, 
    h_freq=80, 
    notch_freq=50, 
    n_versions=3, 
    trials_per_file=5,
    total_channels=15, 
    max_bad_channels=3, 
    min_bad_channels=1,
    do_preprocessing=True,
    do_ica=False,
    do_trial=True,
    n_components=config.ica_components,
    ica_method=config.ica_method,
    random_state=config.ica_seed,
    answer_file=None
):
    
    ica_dir = os.path.join(dataset_dir, 'ica')
    trials_dir = os.path.join(dataset_dir, 'trials')

    # Initialize core storage
    core_path = _init_core_storage(dataset_dir)
    # _init_channel_index_db(core_path)

    # If do_trial is True, we need the 'answer' JSON for channel info
    if do_trial:
        if not answer_file or not os.path.isfile(answer_file):
            print(f"[ERROR] Specified answer file not found or none provided:\n  {answer_file}")
            print("Stopping the program.")
            return
        else:
            with open(answer_file, 'r') as file:
                answer_data = json.load(file)
    else:
        answer_data = {}

    # Print summary
    print(f"\n=== Preprocessing for {channel_types} | do_ica={do_ica} | do_trial={do_trial} ===")
    if do_preprocessing:
        print("\n[PREPROCESSING] Parameters:")
        print(f"  - l_freq      = {l_freq}")
        print(f"  - h_freq      = {h_freq}")
        print(f"  - notch_freq  = {notch_freq}")
        print(f"  - n_components= {n_components}")
        print(f"  - ica_method  = {ica_method}")
        print(f"  - random_state= {random_state}")
        print("")

    data_files = [
        f for f in os.listdir(raw_dir) 
        if not f.startswith('.') # skip hidden files
    ]
    if not data_files:
        print(f"No files found in {raw_dir}. Skipping.")
        return

    pbar = tqdm(data_files, desc="Processing files")
    for data_file in pbar:
        pbar.set_description(f"Processing {data_file[:15]}...")

        # Parse out subj_ses_run from the filename (assuming subj_ses_run_*.fif)
        try:
            subj, ses, run = data_file.split('_')[:3]
        except ValueError:
            print(f"File name {data_file} not in expected subj_ses_run format. Skipping.")
            continue

        print(f"\n--- Processing File: {data_file} (subj={subj}, ses={ses}, run={run}) ---")
        file_path = os.path.join(raw_dir, data_file)

        # -------------------------
        # 1) Load & Filter
        # -------------------------
        raw = mne.io.read_raw(file_path, preload=True, allow_maxshield=True)
        if do_preprocessing:
            freqs = [notch_freq * i for i in range(1, 5)]
            raw.notch_filter(freqs=freqs)
            raw.filter(l_freq=l_freq, h_freq=None, fir_design='firwin')
            raw.filter(l_freq=None, h_freq=h_freq, fir_design='firwin')

        # -------------------------
        # 2) Save entire preprocessed data as FIF
        # -------------------------
        _save_preprocessed_raw_fif(raw, core_path, subj, ses, run) # whatever you were, you are fif now

        # channel_index_info = _save_preprocessed_channels(raw, core_path, subj, ses, run)
        # _save_channel_index_json(core_path, subj, ses, run, channel_index_info)
        # _insert_channel_index(core_path, subj, ses, run, channel_index_info)

        # -------------------------
        # 3) ICA (optional)
        # -------------------------
        if do_ica and channel_types:
            print("[INFO] Running ICA ...")
            for ch_type in channel_types:
                if ch_type:
                    _fit_and_save_ica(
                        raw=raw,
                        ica_save_path=ica_dir,
                        ica_name = f"{subj}_{ses}_{run}_{ch_type}_ica.fif",
                        channel_type=ch_type,
                        n_components=n_components,
                        method=ica_method,
                        random_state=random_state
                    )

        # -------------------------
        # 4) Trials (optional)
        # -------------------------
        if do_trial:
            print("[INFO] Generating Trials ...")
            trial_db_path = os.path.join(core_path, "index_db", "trials.db")
            _init_trial_db(trial_db_path)
            conn = sqlite3.connect(trial_db_path)
            try:
                for version in range(n_versions):
                    for ch_type in channel_types:
                        if ch_type == 'eeg':
                            badC_EEG = answer_data.get("badC_EEG", {})
                            bad_channels = badC_EEG.get(subj, {}).get(ses, {}).get(run, [])
                        else:
                            badC_MEG = answer_data.get("badC_MEG", {})
                            all_meg_bad = badC_MEG.get(subj, {}).get(ses, {}).get(run, [])
                            if ch_type == 'mag':
                                bad_channels = [ch for ch in all_meg_bad if ch.endswith('1')]
                            elif ch_type == 'grad':
                                bad_channels = [ch for ch in all_meg_bad if ch.endswith(('2','3'))]
                            else:
                                bad_channels = []

                        for _ in range(trials_per_file):
                            chs_to_display, bad_chans_in_display = _select_and_shuffle_channels(
                                raw=raw,
                                bad_channels=bad_channels,
                                channel_type=ch_type,
                                total_channels=total_channels,
                                max_bad_channels=max_bad_channels,
                                min_bad_channels=min_bad_channels
                            )
                            all_chs = raw.info['ch_names']

                            if chs_to_display is None:
                                print(f"[WARNING] Skipping trial for {subj}_{ses}_{run}_{ch_type} (not enough bad channels).")
                                continue

                            # # Unique ID from (subj, ses, run, ch_type, version, channel names)
                            trial_id = f"{subj}_{ses}_{run}_{ch_type}_v{version+1}_{hash(tuple(chs_to_display)):x}"

                            conn.execute("""
                                INSERT OR IGNORE INTO trials 
                                (trial_id, subj, ses, run, ch_type, version, chs2display, bad_channels)
                                VALUES (?,?,?,?,?,?,?,?)
                            """, (
                                trial_id,
                                subj,
                                ses,
                                run,
                                ch_type,
                                version+1,
                                pickle.dumps(chs_to_display),
                                pickle.dumps(bad_chans_in_display)
                            ))
                conn.commit()
            finally:
                conn.close()

        # Save dataset-level config each iteration (overwrites each time with current info).
        dataset_config = {
            "sfreq": raw.info["sfreq"],
            "n_channels": len(raw.info["ch_names"]),
            "do_preprocessing": do_preprocessing,
            "l_freq": l_freq if do_preprocessing else None,
            "h_freq": h_freq if do_preprocessing else None,
            "notch_freq": notch_freq if do_preprocessing else None,
            "ica_method": ica_method if do_ica else None,
            "n_components": n_components if do_ica else None,
            "random_state": random_state if do_ica else None,
            "answer_file": answer_file if do_trial else None
        }
        _save_dataset_config(core_path, dataset_config)

    print(f"[DONE] All requested processing complete. (ICA={do_ica}, Trials={do_trial})")
    print("[DONE] You can now remove or archive the raw files if desired.")
