# preparetrials.py
import json
import os
import random
import pickle
import mne

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

def prepare_trials(data_dir, output_dir, n_versions=3, trials_per_file=5):
    """
    Prepares trial data by selecting and shuffling channels, and saves them for experiments.

    Args:
        data_dir (str): Directory containing preprocessed data files.
        output_dir (str): Directory to save trial data.
        n_versions (int): Number of versions to create.
        trials_per_file (int): Number of trials per data file and channel type.
    """
    os.makedirs(output_dir, exist_ok=True)
    data_files = [f for f in os.listdir(data_dir) if f.endswith('_preprocessed_raw.fif')]

    # Load JSON data
    with open('config.json', 'r') as file:
        config_data = json.load(file)

    for version in range(n_versions):
        trial_num = 0
        for data_file in data_files:
            file_path = os.path.join(data_dir, data_file)
            subj, ses, run = data_file.split('_')[:3]
            run_ind = run + '.fif'
            raw_preprocessed = mne.io.read_raw_fif(file_path, preload=True, allow_maxshield=True)

            for channel_type in ['EEG', 'Mag', 'Grad']:
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
                        raw_preprocessed, bad_channels, channel_type
                    )
                    
                    trial_data = raw_preprocessed.copy().pick(channels_to_display)
                    # Pair the trial data with the bad channels
                    # trial_pair = (trial_data, bad_chans_in_display)
                    # trial_filename = f'trial_{trial_num}_{version+1}.pkl'
                    # trial_filepath = os.path.join(output_dir, trial_filename)
                    trial_dict = {
                        "data": trial_data,
                        "bad_chans_in_display": bad_chans_in_display,
                        "channel_type": channel_type
                    }
                    
                    trial_filename = f'trial_{trial_num}_{version+1}_{channel_type}.pkl'
                    trial_filepath = os.path.join(channel_output_dir, trial_filename)

                    print(trial_filename)
                    print(bad_chans_in_display)
                    with open(trial_filepath, 'wb') as f:
                        pickle.dump(trial_dict, f)
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
    data_dir = os.path.join('data', 'preprocessed')
    trials_output_dir = os.path.join('data', 'trial_data')
    sample_output_file = os.path.join('data', 'sampled_trials.pkl')

    prepare_trials(data_dir, trials_output_dir)

    sample_trials(trials_output_dir, sample_output_file)
