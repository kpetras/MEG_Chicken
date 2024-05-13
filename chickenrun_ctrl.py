# chickenrun_ctrl.py

####################
# block for the control group (no feedback)
####################

# %%
# Import packages
import numpy as np
import mne
import tkinter as tk
import threading
import time
from pynput import keyboard
import HelperFuns as hf
import os
import mne
from threading import Thread
import time
from PyQt5.QtWidgets import QApplication
from slides import display_slides

# %%
def on_press(key):
    if key == keyboard.Key.space:
        shared['space_pressed'] = True        
    if key == keyboard.Key.tab:
        shared['tab_pressed'] = True

# Load Preprocessed Data Function 
data_path = 'processed_data\\'  # Directory to save preprocessed files 
fileList = ['FADM9A_session1_run01.fif_preprocessed-raw.fif', '03TPZ5_session2_run01.fif_preprocessed-raw.fif']

# %%
####################
# block for the EEG channel rejection
####################

# Display the slides
slide_folder = r'slides' 
display_slides(slide_folder)

# Load and process files
for file in fileList:
    print('processing file: ', file)
    file_path = os.path.join(data_path, file)
    from config import badC_EEG, badC_MEG, ICA_remove_inds
    filePath_without_ext = os.path.splitext(file)[0]    
    parts = filePath_without_ext.split('_')    
    # Extract subj, ses, run
    subj, ses, run = parts[0], parts[1], parts[2]    
    badC_MEG_list = badC_MEG[subj][ses][run]
    badC_EEG_list = badC_EEG[subj][ses][run]

    if os.path.exists(file_path):
        raw_filtered = mne.io.read_raw_fif(file_path, preload=True, allow_maxshield=True)
        num_channels = raw_filtered.info['nchan']

        fig = raw_filtered.plot(n_channels=10, duration=2, block=False)
        answer = badC_MEG_list + badC_EEG_list

        shared = {
            'done': False,
            'hits': 0,
            'false_alarms': 0,
            'misses': 0,
            'correct_rejections': num_channels
        }

        thread = Thread(target=hf.monitor_bads_no_feedback, args=(fig, answer, shared))
        thread.start()

        # Start listening for key press
        listener = keyboard.Listener(on_press=on_press)
        listener.start()

        # Wait for the thread to finish
        while not shared['done']:
            QApplication.processEvents()
            time.sleep(0.1)

        hits = shared.get('hits')
        false_alarms = shared.get('false_alarms')
        misses = shared.get('misses')
        correct_rejections = shared.get('correct_rejections')

        hf.save_results_bads(subj, ses, run, hits, false_alarms, misses, correct_rejections, 'control')
    else:
        print(f"File {file_path} does not exist.")

# %%
####################
# block for the ICA rejection
####################

import matplotlib
matplotlib.use('Qt5Agg')

data_path = 'fitted_ica\\'
fileList = ['FADM9A_session1_run01.fif_fitted_ica.fif', 'FADM9A_session1_run02.fif_fitted_ica.fif']

chs_type = 'eeg'
n_components_per_page = 50

for file in fileList:
    print('processing file: ', file)
    from config import ICA_remove_inds
    file_path = os.path.join(data_path, file)
    filePath_without_ext = os.path.splitext(file)[0]
    parts = filePath_without_ext.split('_')
    subj, ses, run = parts[0], parts[1], parts[2]
    ICA_remove_inds_list = ICA_remove_inds[subj][run]

    if os.path.exists(file_path):
        ica = mne.preprocessing.read_ica(file_path)
        ica.plot_sources(raw_filtered, block=False)
        fig = ica.plot_components(inst=raw_filtered, picks=range(n_components_per_page))

        answer = ICA_remove_inds_list[chs_type]

        shared = {
            'done': False,
            'hits': 0,
            'false_alarms': 0,
            'misses': 0,
            'correct_rejections': n_components_per_page
        }

        thread = threading.Thread(target=hf.monitor_ICs_no_feedback, args=(ica, answer, shared))
        thread.start()

        while not shared['done']:
            QApplication.processEvents()
            time.sleep(0.1)

        hits = shared.get('hits')
        false_alarms = shared.get('false_alarms')
        misses = shared.get('misses')
        correct_rejections = shared.get('correct_rejections')

        hf.save_results_ICs(subj, ses, run, hits, false_alarms, misses, correct_rejections, 'control')
    else:
        print(f"File {file_path} does not exist.")

# %%
####################
# block for the EEG channel rejection 10 channels at a time 
# with a random number of bad channels included
####################

import random

def select_and_shuffle_channels(raw, bad_channels):
    """Selects and shuffles a list of channels including a random selection of bad ones."""
    all_channels = raw.ch_names
    good_channels = [ch for ch in all_channels if ch not in bad_channels]
    
    # Randomly select 0 to 3 bad channels
    num_bad_channels = random.randint(0, 3)
    selected_bad_channels = random.sample(bad_channels, min(len(bad_channels), num_bad_channels))
    print('Selected bad channels:', selected_bad_channels)

    # Calculate number of good channels needed
    num_good_channels = 15 - len(selected_bad_channels)
    selected_good_channels = random.sample(good_channels, num_good_channels)
    print('Selected good channels:', selected_good_channels)
    
    # Combine and shuffle the final list
    final_selection = selected_good_channels + selected_bad_channels
    random.shuffle(final_selection)
    
    return final_selection

for file in fileList:
    print('processing file: ', file)
    file_path = os.path.join(data_path, file)

    if os.path.exists(file_path):
        raw_filtered = mne.io.read_raw_fif(file_path, preload=True, allow_maxshield=True)
        answer = badC_MEG_list + badC_EEG_list
        
        # Select 15 channels, randomly including up to 3 bad channels
        channels_to_display = select_and_shuffle_channels(raw_filtered, answer)

        # Plot with the specific subset of channels
        fig = raw_filtered.plot(picks=channels_to_display, n_channels=len(channels_to_display), 
                                duration=2, block=False)

        shared = {
            'done': False,
            'hits': 0,
            'false_alarms': 0,
            'misses': 0,
            'correct_rejections': len(channels_to_display)
        }

        thread = Thread(target=hf.monitor_bads_no_feedback, args=(fig, answer, shared))
        thread.start()

        listener = keyboard.Listener(on_press=on_press)
        listener.start()

        while not shared['done']:
            QApplication.processEvents()
            time.sleep(0.1)

        # Retrieve results and save them
        hits = shared.get('hits')
        false_alarms = shared.get('false_alarms')
        misses = shared.get('misses')
        correct_rejections = shared.get('correct_rejections')

        hf.save_results_bads(subj, ses, run, hits, false_alarms, misses, correct_rejections, 'control')
    else:
        print(f"File {file_path} does not exist.")

# %%
