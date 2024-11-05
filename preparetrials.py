# preparetrials.py
import json
import os
import random
import pickle
from HelperFuns import select_and_shuffle_channels
import mne

def prepare_trials(data_dir, output_dir, n_versions=1, trials_per_file=5):
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
            # Added allow_maxshield=True because of ValueError: This file contains raw Internal Active Shielding data. 
            # It may be distorted. Elekta recommends it be run through MaxFilter to produce reliable results. Consider closing the file and running MaxFilter on the data.
            # Use allow_maxshield=True if you are sure you want to load the data despite this warning.
            raw_preprocessed = mne.io.read_raw_fif(file_path, preload=True, allow_maxshield=True)

            for channel_type in ['EEG', 'Mag', 'Grad']:
                if channel_type == 'EEG':
                    # bad_channels = badC_EEG.get(subj, {}).get(ses, {}).get(run, [])
                    badC_EEG = config_data.get("badC_EEG", {})
                    bad_channels = badC_EEG[subj][ses][run_ind]
                else:
                    badC_MEG = config_data.get("badC_MEG", {})
                    bad_channels = badC_MEG[subj][ses][run_ind]
                    if channel_type == 'Mag':
                        bad_channels = [ch for ch in bad_channels if ch.endswith('1')]
                    elif channel_type == 'Grad':
                        bad_channels = [ch for ch in bad_channels if ch.endswith(('2', '3'))]
                print(channel_type)
                for _ in range(trials_per_file):
                    channels_to_display, bad_chans_in_display = select_and_shuffle_channels(
                        raw_preprocessed, bad_channels, channel_type
                    )
                    
                    trial_data = raw_preprocessed.copy().pick(channels_to_display)
                    # Pair the trial data with the bad channels
                    trial_pair = (trial_data, bad_chans_in_display)
                    trial_filename = f'trial_{trial_num}_{version+1}.pkl'
                    trial_filepath = os.path.join(output_dir, trial_filename)
                    print(trial_filename)
                    print(bad_chans_in_display)
                    with open(trial_filepath, 'wb') as f:
                        pickle.dump(trial_pair, f)
                    trial_num += 1

def sample_trials(trial_dir, sample_file, n_samples=10):
    """
    Randomly samples trials from the prepared trial data and saves them.

    Args:
        trial_dir (str): Directory containing prepared trial data.
        sample_file (str): File to save the sampled trials.
        n_samples (int): Number of trials to sample.
    """
    trial_files = [os.path.join(trial_dir, f) for f in os.listdir(trial_dir) if f.startswith('trial_')]
    sampled_files = random.sample(trial_files, min(n_samples, len(trial_files)))

    sampled_trials = []
    for file in sampled_files:
        with open(file, 'rb') as f:
            trial = pickle.load(f)
            sampled_trials.append(trial)

    with open(sample_file, 'wb') as f:
        pickle.dump(sampled_trials, f)
    print(f"Sampled {len(sampled_trials)} trials saved to {sample_file}")

if __name__ == "__main__":
    # Example usage
    data_directory = os.path.join('data', 'preprocessed')
    trials_output_dir = os.path.join('data', 'trial_data')
    sample_output_file = os.path.join('data', 'sampled_trials.pkl')

    prepare_trials(data_directory, trials_output_dir)
    sample_trials(trials_output_dir, sample_output_file)
