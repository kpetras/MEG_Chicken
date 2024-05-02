# chickenrun_ctrl_exp.py
# "write the entire experiment for the control group"

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
#from slides import display_slides # Import the slide presentation function

# %%
# Load Preprocessed Data Function 
data_path = 'processed_data\\'  # Directory to save preprocessed files 
fileList = ['FADM9A_session1_run01.fif_preprocessed-raw.fif', '03TPZ5_session2_run01.fif_preprocessed-raw.fif']


# %%
# or use ICA_remove_inds_concatRuns, but don't wanna bother with concatenation for now

# %%
# Display the slides
from slides import display_slides
slide_folder = r'slides' 
display_slides(slide_folder)


# %%
####################
# block for the control group (no feedback)
####################

# open interactive window
# fig = raw_filtered.plot(n_channels=1, duration=2)

# # close the interactive window when it's done

# # compare and record the results
# response = raw_filtered.info['bads']
# answer = badC_MEG_list + badC_EEG_list

# %%
####################
# block for the experimental group (with feedback)
####################


def on_press(key):
    if key == keyboard.Key.space:
        shared['space_pressed'] = True        
    if key == keyboard.Key.tab:
        shared['tab_pressed'] = True

data_path = 'processed_data\\'  # Directory to save preprocessed files 
fileList = ['FADM9A_session1_run01.fif_preprocessed-raw.fif', '03TPZ5_session2_run01.fif_preprocessed-raw.fif']

for file in fileList:
    print('processing file: ', file)
    # Retrieve bad channels and ICA indices
    # from config import datapath, preprocpath, subjects
    file_path = os.path.join(data_path, file)
    from config import badC_EEG, badC_MEG, ICA_remove_inds
    filePath_without_ext = os.path.splitext(file)[0]    
    parts = filePath_without_ext.split('_')    
    # Extract subj, ses, and run
    subj, ses, run = parts[0], parts[1], parts[2]    
    badC_MEG_list = badC_MEG[subj][ses][run]
    badC_EEG_list = badC_EEG[subj][ses][run]
    #ICA_remove_inds_list = ICA_remove_inds[subj][run]
    # Check if the file exists before trying to load it
    if os.path.exists(file_path):
        # Load the preprocessed data 
        raw_filtered = mne.io.read_raw_fif(file_path, preload=True, allow_maxshield=True)

        # open interactive window
        fig = raw_filtered.plot(n_channels=10, duration=2, block=False)
        print(type(fig))

        # Initialize previous_bads to an empty list
        previous_bads = []
        answer = badC_MEG_list + badC_EEG_list

        # Initialize a counter
        counter = 0

        # Create a shared dictionary
        shared = {'space_pressed': False,
                  'tab_pressed': False,
                  'done': False}

        # Create a new thread that runs the monitor_bads function
        thread = Thread(target=hf.monitor_bads, args=(fig, answer, shared))

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
    hf.save_results(subj, ses, run, hits, false_alarms, misses, correct_rejections)

# # After experiment, retrieve results
# hits, false_alarms, misses, correct_rejections = hf.monitor_bads(fig, answer, shared)

# # Save results
# hf.save_results(subj, ses, run, hits, false_alarms, misses, correct_rejections)

# %%
print('now we are here')
####################
# block for the ICA rejection
####################
import matplotlib
matplotlib.use('Qt5Agg')  # Make sure to use an interactive backend

# Do the ICA decomposition for each sensor type
chs_type = 'eeg' # ['mag', 'grad', 'eeg']
answer = ICA_remove_inds_list[chs_type]

# Fit ICA component
ica = mne.preprocessing.ICA(n_components=50, random_state=42)
ica.fit(raw_filtered, picks = chs_type)

n_components_per_page = 50 # number of components per page

# %%
# Create a shared dictionary
shared = {'space_pressed': False}

# Create a new thread that runs the monitor_bads function
thread = threading.Thread(target=hf.monitor_ICs, args=(ica, answer, shared))

# Start the new thread
thread.start()

# Listen for space key press
def on_press(key):
    if key == keyboard.Key.space:
        shared['space_pressed'] = True

# Start listening for key press
listener = keyboard.Listener(on_press=on_press)
listener.start()

ica.plot_sources(raw_filtered, block=False)
fig = ica.plot_components(inst=raw_filtered, picks=range(n_components_per_page))


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

# %%