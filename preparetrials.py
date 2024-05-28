#%% Import packages
import numpy as np
import mne
import tkinter as tk
import threading
import time
from pynput import keyboard
import HelperFuns as hf
import os
import time
from PyQt5.QtWidgets import QApplication
from slides import display_slides
from config import badC_EEG, badC_MEG, ICA_remove_inds
import random
from sklearn.utils import shuffle
import pickle


data_path = 'processed_data\\'  # Directory to save preprocessed files 
fileList = ['FADM9A_session1_run01.fif_preprocessed-raw.fif', '03TPZ5_session2_run01.fif_preprocessed-raw.fif']

for i in range(10):#preparing 10 versions of the trialsequence for now
    trial_num = 0
    for file in fileList:
        print('Processing file:', file)
        file_path = os.path.join(data_path, file)    
        filePath_without_ext = os.path.splitext(file)[0]
        parts = filePath_without_ext.split('_')
        # Extract subj, ses, run
        subj, ses, run = parts[0], parts[1], parts[2]
        #load data
        raw_filtered = mne.io.read_raw_fif(file_path, preload=True, allow_maxshield=True)

        for file_type in ['EEG', 'Mag', 'Grad']:
            # Get list of bad channels depending on the chosen file type
            if file_type == 'EEG':
                bad_channel_list = badC_EEG[subj][ses][run]
            elif file_type == 'Mag':
                bad_channel_list = [ch for ch in badC_MEG[subj][ses][run] if ch.endswith('1')]
            elif file_type == 'Grad':
                bad_channel_list = [ch for ch in badC_MEG[subj][ses][run] if ch.endswith('2') or ch.endswith('3')]
            else:
                raise ValueError(f"Unexpected file type: {file_type}")
            for trl in range(10):
                channels_to_display, badChansInDisplay = hf.select_and_shuffle_channels(raw_filtered, bad_channel_list, file_type)
                #object containing only the channels to display
                trialData = raw_filtered.copy().pick(channels_to_display)
                # Pair the trial data with the bad channels
                pair = (trialData, badChansInDisplay)
                # Save the pair to disk
                with open(f'trial_data\\trial_{trial_num}_{i+1}.pkl', 'wb') as f:
                    pickle.dump(pair, f)
                trial_num += 1
#%%
# Directory where the trial files are stored
trial_data_dir = 'trial_data\\'

# Get a list of all the trial files
trial_files = [os.path.join(trial_data_dir, file) for file in os.listdir(trial_data_dir) if file.startswith('trial_data')]

# Randomly sample 100 trial files
sampled_files = random.sample(trial_files, 100)

# Initialize list to store the sampled trials
sampled_trials = []

# Load the sampled trials and append them to the list
for file in sampled_files:
    with open(file, 'rb') as f:
        trial = pickle.load(f)
        sampled_trials.append(trial)

# Save the sampled trials to a new file
with open('sampled_trials.pkl', 'wb') as f:
    pickle.dump(sampled_trials, f)