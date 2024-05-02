# preprocessing.py

# %%
import numpy as np
import mne
import os

# %%
def load_and_preprocess_data(path, subj, ses, run, save_path = 'processed_data\\'):
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

    # Create the directory 
    os.makedirs(save_path, exist_ok=True)
        
    save_file = f"{save_path}{fname}_preprocessed-raw.fif"
    raw_filtered.save(save_file, overwrite=True)
    print(f"Preprocessed data saved to: {save_file}")

    return raw_filtered

# %%
def fit_and_save_ica(raw, subj, ses, run, chs_type='eeg', n_components=50, ica_save_path='fitted_ica\\'):
    """
    Fits the ICA components and saves the fitted ICA to a file.

    Args:
        raw (mne.io.Raw): Preprocessed raw data.
        subj (str): Subject identifier.
        ses (str): Session identifier.
        run (str): Run identifier.
        chs_type (str): Channel type to use for ICA fitting. Default is 'eeg'.
        n_components (int): Number of components for ICA decomposition. Default is 50.
        ica_save_path (str): Directory path to save the fitted ICA. Default is 'fitted_ica\\'.

    Returns:
        mne.preprocessing.ICA: Fitted ICA object.
    """

    # Fit ICA component
    ica = mne.preprocessing.ICA(n_components=n_components, random_state=42)
    ica.fit(raw, picks = chs_type)

    # Create the directory if it doesn't exist
    os.makedirs(ica_save_path, exist_ok=True)

    # Define the file name for the fitted ICA
    ica_fname = f"{subj}_{ses}_{run}_fitted_ica.fif"

    # Save the fitted ICA to a file
    ica.save(ica_save_path + ica_fname, overwrite=True)

    print(f"Fitted ICA saved to: {ica_save_path + ica_fname}")

    return ica

# %%
# Define the path to the raw data 
path = 'C:\\Users\\stagaire\\Desktop\\Repository\\data\\'  # or your specific path
# path = 'data/'

# List of files to preprocess
files_raw = [
    {'subj': 'FADM9A', 'ses': 'session1', 'run': 'run01.fif'},
    {'subj': '03TPZ5', 'ses': 'session2', 'run': 'run01.fif'}
]

# Loop over the files
for file in files_raw:
    # Call load_and_preprocess_data and assign the return value to raw_filtered
    load_and_preprocess_data(path, file['subj'], file['ses'], file['run'], 'processed_data\\')

# List of files to fit ICA
files_ica = [
    {'subj': 'FADM9A', 'ses': 'session1', 'run': 'run01.fif'},
    {'subj': 'FADM9A', 'ses': 'session1', 'run': 'run02.fif'}
]

# Loop over the files
for file in files_ica:
    # Call load_and_preprocess_data and assign the return value to raw_filtered
    raw_filtered = load_and_preprocess_data(path, file['subj'], file['ses'], file['run'], 'processed_data\\')

    # Call fit_and_save_ica and assign the return value to ica
    fit_and_save_ica(raw_filtered, file['subj'], file['ses'], file['run'])
# %%
