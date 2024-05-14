# chickenrun_exp.py

####################
# block for the experimental group (with feedback)
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
from pynput import keyboard
import time
from PyQt5.QtWidgets import QApplication
import random

# %%
# Load Preprocessed Data Function 
data_path = 'processed_data\\'  # Directory to save preprocessed files 
fileList = ['FADM9A_session1_run01.fif_preprocessed-raw.fif', '03TPZ5_session2_run01.fif_preprocessed-raw.fif'] 

# %%
####################
# block for the EEG channels rejection
####################

def on_press(key):
    if key == keyboard.Key.space:
        shared['space_pressed'] = True        
    if key == keyboard.Key.tab:
        shared['tab_pressed'] = True

data_path = 'processed_data\\'  # Directory to save preprocessed files 
fileList = ['FADM9A_session1_run01.fif_preprocessed-raw.fif', '03TPZ5_session2_run01.fif_preprocessed-raw.fif']

def select_and_shuffle_channels(raw, bad_channels, channel_type):
    """Selects and shuffles a list of channels of a specific type including a random selection of bad ones."""
    all_channels = raw.ch_names
    # Filter channels based on type (EEG or MEG)
    type_channels = [ch for ch in all_channels if ch.startswith(channel_type)]
    good_channels = [ch for ch in type_channels if ch not in bad_channels]
    
    # Randomly select 0 to 3 bad channels from the type-specific list
    num_bad_channels = random.randint(0, 3)
    selected_bad_channels = random.sample([bc for bc in bad_channels if bc in type_channels], min(len(bad_channels), num_bad_channels))
    print('Selected bad channels:', selected_bad_channels)

    # Calculate number of good channels needed
    num_good_channels = 15 - len(selected_bad_channels)
    selected_good_channels = random.sample(good_channels, num_good_channels)
    print('Selected good channels:', selected_good_channels)
    
    # Combine and shuffle the final list
    final_selection = selected_good_channels + selected_bad_channels
    random.shuffle(final_selection)

    # Create a list indicating whether each channel is good (0) or bad (1)
    channel_status = [0 if ch in selected_good_channels else 1 for ch in final_selection]
    badChansInDisplay = [ch for ch in final_selection if ch in bad_channels]
    return final_selection, badChansInDisplay

for file in fileList:
    print('processing file: ', file)
    # Retrieve bad channels and ICA indices
    # from config import datapath, preprocpath, subjects
    file_path = os.path.join(data_path, file)
    from config import badC_EEG, badC_MEG, ICA_remove_inds
    filePath_without_ext = os.path.splitext(file)[0]    
    parts = filePath_without_ext.split('_')    
    # Extract subj, ses, run
    subj, ses, run = parts[0], parts[1], parts[2]
    file_type = random.choice(['EEG', 'MEG'])
    
    # Get the specific list of bad channels depending on the chosen file type
    bad_channel_list = badC_EEG[subj][ses][run] if file_type == 'EEG' else badC_MEG[subj][ses][run]

    # Check if the file exists before trying to load it
    if os.path.exists(file_path):
        # Load the preprocessed data 
        raw_filtered = mne.io.read_raw_fif(file_path, preload=True, allow_maxshield=True)
        channels_to_display, badChansInDisplay = select_and_shuffle_channels(raw_filtered, bad_channel_list, file_type)

        # open interactive window
        fig = raw_filtered.plot(picks=channels_to_display, n_channels=15, duration=2, block=False)
        print(type(fig))

        # Initialize previous_bads to an empty list
        previous_bads = []

        # Initialize a counter
        counter = 0

        # Create a shared dictionary
        shared = {'space_pressed': False,
                  'tab_pressed': False,
                  'done': False,
                  'hits': 0,
                  'false_alarms': 0,
                  'misses': 0,
                  'correct_rejections': len(channels_to_display)}

        # Create a new thread that runs the monitor_bads function
        thread = Thread(target=hf.monitor_bads, args=(fig, badChansInDisplay, shared))

        # Start the new thread
        thread.start()

        # Start listening for key press
        listener = keyboard.Listener(on_press=on_press)
        listener.start()

        # Wait for the thread to finish
        while not shared['done']:
            # Process the GUI event loop
            QApplication.processEvents()
            # Sleep for a short time to reduce CPU usage
            time.sleep(0.1)
        
        print('we are here')
    else:
        print(f"File {file_path} does not exist.")
    
    # After the thread has finished, get the results
    hits = shared.get('hits')
    false_alarms = shared.get('false_alarms')
    misses = shared.get('misses')
    correct_rejections = shared.get('correct_rejections')

    # Save results
    hf.save_results_bads(subj, ses, run, hits, false_alarms, misses, correct_rejections, 'experimental')
    
# %%
####################
# block for the ICA rejection
####################

import matplotlib
matplotlib.use('Qt5Agg')  # Make sure to use an interactive backend

# Listen for space key press
def on_press(key):
    if key == keyboard.Key.space:
        shared['space_pressed'] = True
    if key == keyboard.Key.tab:
        shared['tab_pressed'] = True

data_path = 'fitted_ica\\'  # Directory to save fitted ica files 
fileList = ['FADM9A_session1_run01.fif_fitted_ica.fif', 'FADM9A_session1_run02.fif_fitted_ica.fif']

# Do the ICA decomposition for each sensor type
chs_type = 'eeg' # ['mag', 'grad', 'eeg']
n_components_per_page = 50 # number of components per page

for file in fileList:
    print('processing file: ', file)
    # Retrieve bad channels and ICA indices
    # from config import datapath, preprocpath, subjects
    from config import ICA_remove_inds
    file_path = os.path.join(data_path, file)
    filePath_without_ext = os.path.splitext(file)[0]    
    parts = filePath_without_ext.split('_')    
    # Extract subj, ses, and run
    subj, ses, run = parts[0], parts[1], parts[2]
    ICA_remove_inds_list = ICA_remove_inds[subj][run]

    # Check if the file exists before trying to load it
    if os.path.exists(file_path):
    # Load the fitted ICA
        ica = mne.preprocessing.read_ica(file_path)

        ica.plot_sources(raw_filtered, block=False)
        #fig = ica.plot_components(inst=raw_filtered, picks=range(n_components_per_page))

        # Initialize previous_ICs to an empty list
        previous_bads = []
        answer = ICA_remove_inds_list[chs_type]

        # Initialize a counter
        counter = 0

        # Create a shared dictionary
        shared = {'space_pressed': False, 
                  'tab_pressed': False,
                  'done': False,
                  'hits': 0,
                  'false_alarms': 0,
                  'misses': 0,
                  'correct_rejections': n_components_per_page}

        # Create a new thread that runs the monitor_bads function
        thread = threading.Thread(target=hf.monitor_ICs, args=(ica, answer, shared))

        # Start the new thread
        thread.start()

        # Start listening for key press
        listener = keyboard.Listener(on_press=on_press)
        listener.start()

        # Wait for the thread to finish
        while not shared['done']:
            # Process the GUI event loop
            QApplication.processEvents()
            # Sleep for a short time to reduce CPU usage
            time.sleep(0.1)

        fig = ica.plot_components(inst=raw_filtered, picks=range(n_components_per_page))

        print('we are here')
    else:
        print(f"File {file_path} does not exist.")

    # After the thread has finished, get the results
    hits = shared.get('hits')
    false_alarms = shared.get('false_alarms')
    misses = shared.get('misses')
    correct_rejections = shared.get('correct_rejections')

    # Save results
    hf.save_results_ICs(subj, ses, run, hits, false_alarms, misses, correct_rejections, 'experimental')

# %%
# prepare the epochs
# events = mne.find_events(
#     raw_filtered, stim_channel="STI101", shortest_event=5, min_duration=0.002,initial_event=True
#     )

# event_dict = {
#     "stand": 12,
#     "travIN": 22,
#     "travOut": 11,
# }

# epochs = mne.Epochs(raw_filtered, events, tmin=-1, tmax=3, event_id=event_dict, preload=True)
# epochs["stand"].compute_psd(fmax= 80).plot(picks="meg", exclude="bads")

# epochs_decimated = epochs.decimate(2)  # decimate to 500 Hz
