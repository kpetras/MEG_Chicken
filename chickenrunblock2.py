# %%
from scipy.io import loadmat
import mne
from mne.preprocessing import ICA
import numpy as np
import matplotlib.pyplot as plt

# %%
# Load MATLAB file
mat_data = loadmat('/Users/coline/Desktop/datamatlab/SO_02_00_S01_T00_compdat.mat')

# Extract the data and channel names
eeg_data = mat_data['dat'][0,0]['trial'][0,0]/ 1e6 
channel_names = [str(ch[0]) for ch in mat_data['dat'][0,0]['label']]

# Remove extra characters from channel names
channel_names = [name.replace("['", "").replace("']", "") for name in channel_names]

# Define the sample rate
sfreq = mat_data['dat'][0,0]['fsample'][0,0]  # Extract sample rate from the data

# Create the info structure needed by MNE
info = mne.create_info(channel_names, sfreq, ch_types='eeg')

# Create the RawArray object
raw = mne.io.RawArray(eeg_data, info)

print(raw.info)
print(raw._data.shape)

# Plot the raw data
raw.plot(n_channels=42, duration=5)

# Define a mapping from channel names to new channel types
channel_types = {
    'Lower VEOG': 'eog', 
    'Upper VEOG': 'eog', 
    'Left HEOG': 'eog', 
    'Right HEOG': 'eog', 
    'Offline reference': 'misc'
}

# Set the channel types
raw.set_channel_types(channel_types)

# Set the electrode montage
raw.set_montage('standard_1005')  

# Run ICA with runica method
ica = mne.preprocessing.ICA(n_components=37, method='infomax')
ica.fit(raw)

# Plot components to review and identify artifacts
ica.plot_components()
# %%
