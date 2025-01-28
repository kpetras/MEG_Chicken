# preproc_funcs.py
# functions used for preprocessing
import os
import mne
import json
import random
import pickle
import config

# -------------------------------
#           ICA
# -------------------------------
def fit_and_save_ica(
    raw,  # always "data/raw" 
    ica_save_path, # data/datasetName/ica
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
    ica_ch_save_path = os.path.join(ica_save_path,channel_type)
    os.makedirs(ica_ch_save_path, exist_ok=True)
    ica.save(os.path.join(ica_ch_save_path,ica_name), overwrite=True)
    print(f"[ICA] {channel_type} saved to {os.path.join(ica_ch_save_path,ica_name)}")


# -------------------------------
#     SELECT AND SHUFFLE 
# -------------------------------
def select_and_shuffle_channels(
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
# PREPROCESS + MAKE TRIALS + ICA
# -------------------------------
def preprocess_and_make_trials(
    raw_dir, # always "data/raw" 
    dataset_dir, # data/datasetName/
    channel_types,
    l_freq=0.1, 
    h_freq=80, 
    notch_freq=50, 
    n_versions=3, 
    trials_per_file=5,
    total_channels=15, 
    max_bad_channels=3, 
    min_bad_channels=1,
    do_preprocessing = True,
    do_ica=False,
    do_trial=True,
    n_components=config.ica_components,
    ica_method=config.ica_method,
    random_state=config.ica_seed,
    answer_file=None
):
    
    preprocessed_dir = os.path.join(dataset_dir, 'preprocessed')
    ica_dir = os.path.join(dataset_dir, 'ica')
    trials_dir = os.path.join(dataset_dir, 'trials')


    # If do_trial is True, we absolutely need the 'answer' JSON and it should be there already
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

    # Print all preprocessing params (only if do_preprocessing is True).
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
        if not f.startswith('.') #if not hidden
    ]
    if not data_files:
        print(f"No files found in {raw_dir}. Skipping.")
        return

    for data_file in data_files:
        file_path = os.path.join(raw_dir, data_file)

        # Try to parse out subj_ses_run from the filename
        # Assumed convention subj_ses_run_whatever.as_long_as_mne_likes_it
        try:
            subj, ses, run = data_file.split('_')[:3]
        except ValueError:
            print(f"File name {data_file} not in expected subj_ses_run format. Skipping.")
            continue

        print(f"\n--- Processing File: {data_file} (subj={subj}, ses={ses}, run={run}) ---")

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
        # 2) ICA (optional)
        # -------------------------
        if do_ica and channel_types:
            print("[INFO] Running ICA ...")
            for ch_type in channel_types:
                if ch_type:
                    ica_save_path = ica_dir
                    fit_and_save_ica(
                        raw=raw,
                        ica_save_path=ica_save_path,
                        ica_name = f"{subj}_{ses}_{run}_{ch_type}_ica.fif",
                        channel_type=ch_type,
                        n_components=n_components,
                        method=ica_method,
                        random_state=random_state
                    )
            # Force save preprocessed raw files in .fif format for ICA plot_properties
            preprocessed_filename = f"{subj}_{ses}_{run}_preprocessed_raw.fif"
            os.makedirs(preprocessed_dir, exist_ok=True)
            preprocessed_save_path = os.path.join(preprocessed_dir, preprocessed_filename)
            
            raw.save(preprocessed_save_path, overwrite=True)
            print(f"Preprocessed raw saved at: {preprocessed_save_path}")
        # -------------------------
        # 3) Trials (optional)
        # -------------------------
        if not do_trial:
            # If user doesn't want trials, skip
            continue

        print("[INFO] Generating Trials ...")
        trial_num = 0
        for version in range(n_versions):
            for ch_type in channel_types:
                # Distinguish bad channels
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

                ch_out_dir = os.path.join(trials_dir, ch_type)
                os.makedirs(ch_out_dir, exist_ok=True)

                for _ in range(trials_per_file):
                    chs_to_display, bad_chans_in_display = select_and_shuffle_channels(
                        raw=raw,
                        bad_channels=bad_channels,
                        channel_type=ch_type,
                        total_channels=total_channels,
                        max_bad_channels=max_bad_channels,
                        min_bad_channels=min_bad_channels
                    )
                    trial_data = raw.copy().pick(chs_to_display)
                    
                    trial_dict = {
                        "data": trial_data,
                        "bad_chans_in_display": bad_chans_in_display,
                        "channel_type": ch_type
                    }

                    trial_filename = f"{subj}_{ses}_{run}_trial_{trial_num}_{version+1}_{ch_type}.pkl"
                    trial_filepath = os.path.join(ch_out_dir, trial_filename)
                    with open(trial_filepath, 'wb') as f:
                        pickle.dump(trial_dict, f)
                    
                    print(f" -> Saved: {trial_filename} | bad={bad_chans_in_display}")
                    trial_num += 1

    print(f"[DONE] All requested processing complete. (ICA={do_ica}, Trials={do_trial})")
    print(f"[DONE] You can now remove the raw files.")
