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

# Load Preprocessed Data Function 
data_path = 'processed_data\\'  # Directory to save preprocessed files 
fileList = ['FADM9A_session1_run01.fif_preprocessed-raw.fif', '03TPZ5_session2_run01.fif_preprocessed-raw.fif']

for i in range(10):#preparing 10 versions of the trialsequence for now
    # Initialize lists to store the trial data and bad channels
    all_trials = []
    all_bad_channels = []
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
                all_trials.append(trialData)
                all_bad_channels.append(badChansInDisplay)
    #randomize the trial order (making sure that the bad channels are still associated with the correct trial by pairing them)
    paired = list(zip(all_trials, all_bad_channels))
    # Shuffle the pairs
    random.shuffle(paired)
    # Save the paired list to disk
    with open(f'trial_data\\trial_data_{i+1}.pkl', 'wb') as f:
        pickle.dump(paired, f)
#%%