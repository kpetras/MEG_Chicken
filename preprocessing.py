# preprocessing.py

import numpy as np
import mne
import os

# Define the path to the raw data and the file name
path = 'C:\\Users\\stagaire\\Desktop\\Repository\\data\\'  # or your specific path
# path = 'data/'
subj = 'FADM9A'
ses = 'session1'
run = 'run01.fif'
save_path = 'processed_data\\'  # Directory to save the preprocessed files

def load_and_preprocess_data(path, subj, ses, run, save_path=None):
    """
    Loads and preprocesses the raw data by applying filters.

    Args:
        path (str): Directory path where the raw data files are located.
        subj (str): Subject identifier.
        ses (str): Session identifier.
        run (str): Run identifier.
        save_path (str): Directory path to save the preprocessed data.

    Returns:
        mne.io.Raw: Preprocessed raw data.
    """

    # Build the file name
    fname = subj + '_' + ses + '_' + run
    fname_with_path = path + fname

    # Load the raw data
    raw = mne.io.read_raw_fif(fname_with_path, preload=True, allow_maxshield=True)

    # Filtering parameters
    l_freq = 0.1  # high pass
    notch_freq = 50  # notch
    h_freq = 80  # low pass

    # Apply notch filter
    freqs = (notch_freq, notch_freq * 2, notch_freq * 3, notch_freq * 4)
    raw_filtered = raw.copy().notch_filter(freqs=freqs)

    # High-pass filter
    raw_filtered.filter(l_freq=l_freq, h_freq=None, fir_design="firwin", fir_window="hamming")

    # Low-pass filter
    raw_filtered.filter(l_freq=None, h_freq=h_freq, fir_design="firwin", fir_window="hamming")

    # Save the preprocessed data
    if save_path:
        # Create the directory 
        os.makedirs(save_path, exist_ok=True)
        
        save_file = f"{save_path}{fname}_preprocessed-raw.fif"
        raw_filtered.save(save_file, overwrite=True)
        print(f"Preprocessed data saved to: {save_file}")
    
    # Save num_channels to a file
    num_channels = raw_filtered.info['nchan']

    with open('num_channels.txt', 'w') as f:
        f.write(str(num_channels))

    return raw_filtered

load_and_preprocess_data(path, subj, ses, run, 'processed_data\\')