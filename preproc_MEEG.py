import os
import mne
import json
import random
import pickle

def select_and_shuffle_channels(raw, bad_channels, channel_type, total_channels=15, max_bad_channels=3, min_bad_channels = 1):
    """
    Selects and shuffles channels of a specific type, including a random selection of bad ones.

    Args:
        raw (mne.io.Raw): Raw data.
        bad_channels (list): List of known bad channels.
        channel_type (str): Type of channels to select ('EEG', 'Mag', 'Grad').
        total_channels (int): Total number of channels to select.
        max_bad_channels (int): Maximum number of bad channels to include.

    Returns:
        tuple: (selected_channels, bad_chans_in_display)
    """
    all_channels = raw.ch_names

    # Filter channels by type
    if channel_type == 'EEG':
        type_channels = [ch for ch in all_channels if ch.startswith('EEG')]
    elif channel_type == 'Mag':
        type_channels = [ch for ch in all_channels if ch.startswith('MEG') and ch.endswith('1')]
    elif channel_type == 'Grad':
        type_channels = [ch for ch in all_channels if ch.startswith('MEG') and ch.endswith(('2', '3'))]

    # Separate good and bad channels
    good_channels = [ch for ch in type_channels if ch not in bad_channels]
    bad_channels_in_type = [ch for ch in bad_channels if ch in type_channels]

    # Randomly select bad channels
    num_bad = min(random.randint(min_bad_channels, max_bad_channels), len(bad_channels_in_type))
    selected_bad_channels = random.sample(bad_channels_in_type, num_bad)

    # Randomly select good channels
    num_good = total_channels - num_bad
    selected_good_channels = random.sample(good_channels, min(num_good, len(good_channels)))

    # Combine and shuffle
    selected_channels = selected_good_channels + selected_bad_channels
    random.shuffle(selected_channels)

    return selected_channels, selected_bad_channels

def preprocess_and_make_trials(data_dir, output_dir, l_freq=0.1, h_freq=80, notch_freq=50, 
                             n_versions=3, trials_per_file=5,
                             total_channels=15, max_bad_channels=3, min_bad_channels = 1,
                             channel_types = None):
    '''
    Read raw files directly to avoid any export format issues
    '''
    with open('config.json', 'r') as file:
        config_data = json.load(file)

    data_files = [f for f in os.listdir(data_dir) if not f.startswith('.')]    
    
    for data_file in data_files:
        file_path = os.path.join(data_dir, data_file)
        subj, ses, run = data_file.split('_')[:3]
        run_ind = run + '.fif'
        print(f"\n--- Processing File: {data_file} (subj={subj}, ses={ses}, run={run}) ---")

        # =================================
        #           Preprocessing
        # =================================
        # Load raw data
        raw = mne.io.read_raw(file_path, preload=True, allow_maxshield=True)

        # Apply notch filter to remove power line noise and harmonics
        freqs = [notch_freq * i for i in range(1, 5)]  # [50, 100, 150, 200]
        raw.notch_filter(freqs=freqs)

        # Apply high-pass filter
        raw.filter(l_freq=l_freq, h_freq=None, fir_design='firwin')

        # Apply low-pass filter
        raw.filter(l_freq=None, h_freq=h_freq, fir_design='firwin')
        
        # =================================
        #           Prepare Trials
        # =================================           
        trial_num = 0
        for version in range(n_versions):                
            for channel_type in channel_types:
                if channel_type == 'EEG':
                    badC_EEG = config_data.get("badC_EEG", {})
                    bad_channels = badC_EEG[subj][ses][run_ind]
                else:
                    badC_MEG = config_data.get("badC_MEG", {})
                    bad_channels = badC_MEG[subj][ses][run_ind]
                    if channel_type == 'Mag':
                        bad_channels = [ch for ch in bad_channels if ch.endswith('1')]
                    elif channel_type == 'Grad':
                        bad_channels = [ch for ch in bad_channels if ch.endswith(('2', '3'))]
                
                # Create output directories based one channel type
                channel_output_dir = os.path.join(output_dir, channel_type)
                os.makedirs(channel_output_dir, exist_ok=True)
                
                for _ in range(trials_per_file):
                    channels_to_display, bad_chans_in_display = select_and_shuffle_channels(
                        raw, bad_channels, channel_type, total_channels=15, max_bad_channels=3, min_bad_channels = 1
                    )
                    
                    trial_data = raw.copy().pick(channels_to_display)
                    # Pair the trial data with the bad channels
                    trial_dict = {
                        "data": trial_data,
                        "bad_chans_in_display": bad_chans_in_display,
                        "channel_type": channel_type
                    }
                    
                    trial_filename = f'trial_{trial_num}_{version+1}_{channel_type}.pkl'
                    trial_filepath = os.path.join(channel_output_dir, trial_filename)

                    with open(trial_filepath, 'wb') as f:
                        pickle.dump(trial_dict, f)
                    print(f"  -> Saved: {trial_filename} | bad={bad_chans_in_display}")

                    trial_num += 1    

def sample_trials(trial_dir, sample_file, n_samples=50):
    """
    Randomly samples trials from the prepared trial data and saves them.

    Args:
        trial_dir (str): Directory containing prepared trial data.
        sample_file (str): File to save the sampled trials.
        n_samples (int): Number of trials to sample.
    """
    # Get all trial files from all dir
    all_trial_files = []
    for root, dirs, files in os.walk(trial_dir):
        for f in files:
            if f.startswith('trial_') and f.endswith('.pkl'):
                all_trial_files.append(os.path.join(root, f))
    
    sampled_files = random.sample(all_trial_files, min(n_samples, len(all_trial_files)))

    sampled_trials = []
    for file in sampled_files:
        with open(file, 'rb') as f:
            trial_dict = pickle.load(f)
            sampled_trials.append(trial_dict)

            print(f"Sampled file: {os.path.basename(file)}; channel_type={trial_dict['channel_type']}")

    with open(sample_file, 'wb') as f:
        pickle.dump(sampled_trials, f)
    print(f"Sampled {len(sampled_trials)} trials saved to {sample_file}")

if __name__ == "__main__":
    data_dir = os.path.join('data', 'raw')
    output_dir = os.path.join('data', 'trials')
    ica_dir = os.path.join('data', 'ica') 


    preprocess_and_make_trials(
        data_dir=data_dir,
        output_dir=output_dir,
        l_freq=0.1,
        h_freq=80,
        notch_freq=50,
        n_versions=3,
        trials_per_file=5,
        total_channels=15, 
        max_bad_channels=3, 
        min_bad_channels = 1,
        channel_types=['EEG', 'Mag', 'Grad']
    )

    sample_file = 'sampled_trials.pkl'
    sample_trials(trial_dir=output_dir, sample_file=sample_file, n_samples=50)