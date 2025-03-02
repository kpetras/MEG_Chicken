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
│   │   ├── *.fif # Preprocessed fif files         
│   │   └── index_db/            
│   │       └── trials.db  
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
from tqdm import tqdm
import config
from chickencode import layeggs

# -------------------------------
#           Core Dataset
# -------------------------------


def _save_dataset_config(core_path, dataset_config):
    config_file = os.path.join(core_path, "dataset_config.json")
    with open(config_file, 'w') as f:
        json.dump(dataset_config, f, indent=2)
    print(f"[DATASET CONFIG] Configuration saved at: {config_file}")

# ------------------------------------------
#   Saving the Entire Preprocessed Raw .fif
# ------------------------------------------
def _save_preprocessed_raw_fif(raw, preproc_path, data_file):
    """
    Name change: original_fname = "subj_ses_run.fif" -> "subj_ses_run_preproc_raw.fif"
    """
    preproc_name = f"{data_file[:-4]}_preproc.fif"
    save_path = os.path.join(preproc_path, preproc_name)
    raw.save(save_path, overwrite=True)
    print(f"[SAVED PREPROCESSED] {save_path}")


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
def prepare_chickenrun(
    raw_dir,  # always "data/raw" 
    channel_types,
    data_file,
    answer_file=None,
    l_freq=0.1, 
    h_freq=80, 
    notch_freq=50, 
    total_channels=15, 
    max_bad_channels=3, 
    min_bad_channels=1,
    do_preprocessing=True,
    do_ica=False,
    do_ans = True,
    pick_bad_channels = True,
    pick_bad_components = True,
    n_components=config.ica_components,
    ica_method=config.ica_method,
    random_state=config.ica_seed,
):
    
    ica_dir = config.ica_dir

    # If do_ans is True, we need the 'answer' JSON 
    if do_ans:
        with open(os.path.join(config.answer_dir, answer_file), 'r') as file:
            answer_data = json.load(file)

    # Print summary
    print(f"\n=== Preprocessing for {channel_types} | do_ica={do_ica}")
    if do_preprocessing:
        print("\n[PREPROCESSING] Parameters:")
        print(f"  - l_freq      = {l_freq}")
        print(f"  - h_freq      = {h_freq}")
        print(f"  - notch_freq  = {notch_freq}")
        print(f"  - n_components= {n_components}")
        print(f"  - ica_method  = {ica_method}")
        print(f"  - random_state= {random_state}")
        print("")
   
    print(f"Processing {data_file}...")

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
    _save_preprocessed_raw_fif(raw, config.preproc_dir, data_file) # whatever you were, you are fif now

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
                    ica_name = f"{data_file[:-4]}_ica.fif",
                    channel_type=ch_type,
                    n_components=n_components,
                    method=ica_method,
                    random_state=random_state
                )
    # -------------------------
    # 4) Answers (optional)
    # -------------------------
    if do_ans:
        cmds = []
        if channel_types:
            cmds.append('meeg')
        if do_ica:
            cmds.append('ica')
        layeggs.makeAns(cmds, answer_file, data_file, pick_bad_channels, pick_bad_components)
        
        
    
    print(f"[DONE] All requested processing complete.")
