# preprocessing.py

import os
import mne

def load_and_preprocess_data(raw_filepath, l_freq=0.1, h_freq=80, notch_freq=50):
    """
    Loads raw data and applies preprocessing steps: notch filter, high-pass filter, and low-pass filter.

    Args:
        raw_filepath (str): Full path to the raw data file. example: 2XXX72_session1_run01_raw.fif
        l_freq (float): Low cutoff frequency for high-pass filter.
        h_freq (float): High cutoff frequency for low-pass filter.
        notch_freq (float): Frequency for notch filter to remove power line noise.

    Returns:
        mne.io.Raw: Preprocessed raw data.
    """
    # Load raw data
    # raw = mne.io.read_raw_fif(raw_filepath, preload=True, allow_maxshield=True)
    raw = mne.io.read_raw(raw_filepath, preload=True, allow_maxshield=True)

    # Apply notch filter to remove power line noise and harmonics
    freqs = [notch_freq * i for i in range(1, 5)]  # [50, 100, 150, 200]
    raw.notch_filter(freqs=freqs)

    # Apply high-pass filter
    raw.filter(l_freq=l_freq, h_freq=None, fir_design='firwin')

    # Apply low-pass filter
    raw.filter(l_freq=None, h_freq=h_freq, fir_design='firwin')

    # It is critical to mark bad channels in raw.info['bads']
    # prior to processing in order to prevent artifact spreading. 
    # Manual inspection and use of find_bad_channels_maxwell() is recommended.
    # raw.preprocessing.maxwell_filter()
    return raw

def fit_and_save_ica(raw, ica_save_path, channel_type = ['mag', 'grad', 'eeg'],
                     n_components=50, method='fastica', random_state=42):
    """
    Fits ICA to the raw data for a given channel type (EEG / Mag / Grad) and saves to a file.

    Args:
        raw (mne.io.Raw): Preprocessed raw data.
        ica_save_path (str): Path to save the fitted ICA object.
        channel_type (str): 'EEG', 'Mag', or 'Grad'.
        n_components (int): Number of ICA components.
        method (str): ICA method ('fastica', 'infomax', etc.).
        random_state (int): random seed for reproducibility.
    """
    if channel_type == 'eeg':
        picks = ['eeg']
    elif channel_type == 'mag':
        picks = ['mag']
    elif channel_type == 'grad':
        picks = ['grad']
    else:
        picks = ['mag', 'grad', 'eeg']

    ica = mne.preprocessing.ICA(
        n_components=n_components, 
        method=method, 
        random_state=random_state
    )
    ica.fit(raw, picks=picks)

    os.makedirs(os.path.dirname(ica_save_path), exist_ok=True)

    ica.save(ica_save_path, overwrite=True)
    print(f"[{channel_type}] ICA saved to {ica_save_path}")

def save_raw_data(raw, save_path):
    """
    Saves the raw data to a file.

    Args:
        raw (mne.io.Raw): Raw data to save.
        save_path (str): Path to save the raw data file.
    """
    # Ensure the save directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # Save the raw data
    raw.save(save_path, overwrite=True)
    print(f"Preprocessed data saved to {save_path}")

if __name__ == "__main__":
    data_dir = os.path.join('data', 'raw')  # Raw data directory
    save_dir = os.path.join('data', 'preprocessed')  # Processed data directory
    ica_dir = os.path.join('data', 'ica')  # ICA save directory

    raw_filenames = [f for f in os.listdir(data_dir) if not f.startswith('.')]

    channel_types = ["eeg", "mag", "grad"]

    for raw_filename in raw_filenames:
        raw_filepath = os.path.join(data_dir, raw_filename)

        preprocessed_raw = load_and_preprocess_data(raw_filepath)

        preprocessed_filename = raw_filename.replace('_raw.fif', '_preprocessed_raw.fif')
        preprocessed_save_path = os.path.join(save_dir, preprocessed_filename)
        save_raw_data(preprocessed_raw, preprocessed_save_path)

        for ch_type in channel_types:
            ica_filename = raw_filename.replace('_raw.fif', f'_{ch_type}_ica.fif')

            ch_ica_dir = os.path.join(ica_dir, ch_type)
            ica_save_path = os.path.join(ch_ica_dir, ica_filename)

            fit_and_save_ica(
                preprocessed_raw, 
                ica_save_path=ica_save_path, 
                channel_type=ch_type
            )