# %%
from scipy.io import loadmat
import mne
import numpy as np
import matplotlib.pyplot as plt

# %%
# Load MATLAB file
mat_data = loadmat('/Users/coline/Desktop/datamatlab/SO_02_00_S01_T00_compdat.mat')

# Extract the data and channel names
eeg_data = mat_data['dat'][0,0]['trial'][0,0]/10000
channel_names = [str(ch[0]) for ch in mat_data['dat'][0,0]['label']]

# Define the sample rate
sfreq = mat_data['dat'][0,0]['fsample'][0,0]  # Extract sample rate from the data

# Create the info structure needed by MNE
info = mne.create_info(channel_names, sfreq, ch_types='eeg')

# Create the RawArray object
raw = mne.io.RawArray(eeg_data, info)

print(raw.info)
print(raw._data.shape)

# Plot the raw data
raw.plot(n_channels=42, duration=1)

# %%
