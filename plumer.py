# %%
# Import packages
import matplotlib.pyplot as plt
import numpy as np
import mne
import random
import tempfile
import time 

# %%
# Load EEG data
path = '/Users/coline/Desktop/Internship/03TPZ5_session2_run01.fif'
raw = mne.io.read_raw_fif(path, preload=True, allow_maxshield=True)

# %%
# Filtering (cutoff frequency in Hz)
lowpass_freq = .5
highpass_freq = 40
raw_filtered = raw.copy().filter(l_freq=lowpass_freq, h_freq=None, fir_design='firwin')
raw_filtered.filter(l_freq=None, h_freq=highpass_freq)

# %%
# Resampling, labelling channels
# Downsample the data 
raw_filtered.resample(250, npad="auto")

# Add channels to the list of "bad datas" 
channels_to_mark_as_bad = ['MEG0332','MEG1022','MEG1143','MEG1242','MEG1333','MEG1433','MEG2013','MEG2023','MEG2413','MEG2623','MEG0121','MEG1931']
raw_filtered.info['bads'].extend(channels_to_mark_as_bad)

# Save the preprocessed data
raw_filtered.save('/Users/coline/Desktop/Internship/tempfile.fif', overwrite=True)
