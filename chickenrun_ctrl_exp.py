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
#from slides import display_slides # Import the slide presentation function

# %%
# Load Preprocessed Data Function 

def load_preprocessed_data(data_path, subj, ses, run): 
    """ 
    Loads preprocessed data from a specified directory. 
    
    Args: 
        data_path (str): Directory path where the preprocessed files are located. 
        subj (str): Subject identifier. 
        ses (str): Session identifier. 
        run (str): Run identifier. 

    Returns: 
        mne.io.Raw: Preprocessed raw data. 
    """ 
    
    fname = f"{subj}_{ses}_{run}_preprocessed-raw.fif" 
    fname_with_path = f"{data_path}{fname}" 
    
    return mne.io.read_raw_fif(fname_with_path, preload=True, allow_maxshield=True) 

# File paths and identifiers 
data_path = 'processed_data/' # Directory to save preprocessed files 
subj = 'FADM9A' 
ses = 'session1' 
run = 'run01.fif' 

# Load the preprocessed data 
raw_filtered = load_preprocessed_data(data_path, subj, ses, run)

# %%
# Retrieve bad channels and ICA indices
# from config import datapath, preprocpath, subjects
from config import badC_EEG, badC_MEG, ICA_remove_inds
badC_MEG_list = badC_MEG[subj][ses][run]
badC_EEG_list = badC_EEG[subj][ses][run]
ICA_remove_inds_list = ICA_remove_inds[subj][run]
# or use ICA_remove_inds_concatRuns, but don't wanna bother with concatenation for now

# %%
# Display the slides
from slides import display_slides
slide_folder = r'slides' 
display_slides(slide_folder)

# %%
# # Load Laetitia's data and labels
# path  = 'C:\\Users\\stagaire\\Desktop\\local\\data\\'
# # path = '/Users/elizabeth/Desktop/MEGChicken/'
# subj = 'FADM9A'
# ses = 'session1'
# run = 'run01.fif'
# fname = subj + '_' + ses + '_' + run
# fname_with_path = path + fname
# raw = mne.io.read_raw_fif(fname_with_path, preload=True, allow_maxshield=True)

# %%
# filtering
# # filter parameters
# l_freq = 0.1 # high pass
# notch_freq = 50  # notch
# h_freq = 80  # low pass

# freqs = (notch_freq, notch_freq*2, notch_freq*3, notch_freq*4)
# raw_filtered = raw.copy().notch_filter(freqs=freqs)
# # high pass filter
# raw_filtered.filter(
#     l_freq=l_freq, h_freq=None, fir_design="firwin", fir_window="hamming"
#     )
# # low pass filter
# raw_filtered.filter(
#     l_freq=None, h_freq=h_freq, fir_design="firwin", fir_window="hamming"
#     )
# # raw_filtered.plot(n_channels=15, duration=2)

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

# Listen for space key press
def on_press(key):
    if key == keyboard.Key.space:
        shared['space_pressed'] = True        
    if key == keyboard.Key.tab:
        shared['tab_pressed'] = True
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
thread = threading.Thread(target=hf.monitor_bads, args=(fig, answer, shared))

# Start the new thread
thread.start()

# Start listening for key press
listener = keyboard.Listener(on_press=on_press)
listener.start()

# while not shared.get('done', False):
#     time.sleep(.1)
if shared.get('done', False):    
    print('we are here')

# After experiment, retrieve results
hits, false_alarms, misses, correct_rejections = monitor_bads(fig, bad_channels_list, shared)

# Save results
save_results(subj, ses, run, hits, false_alarms, misses, correct_rejections)

# %%
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