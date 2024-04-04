# chickenrun_ctrl_exp.py
# "write the entire experiment for the control group"

# %%
# Import packages
import numpy as np
import mne
import tkinter as tk
import threading

# %%
# Load Laetitia's data and labels
path  = '/Users/elizabeth/Desktop/MEGChicken/'
subj = '03TPZ5'
ses = 'session2'
run = 'run01.fif'
fname = subj + '_' + ses + '_' + run
fname_with_path = path + fname
raw = mne.io.read_raw_fif(fname_with_path, preload=True, allow_maxshield=True)

# from config import datapath, preprocpath, subjects
from config import badC_EEG, badC_MEG, ICA_remove_inds
badC_MEG_list = badC_MEG[subj][ses][run]
badC_EEG_list = badC_EEG[subj][ses][run]

# %%
# preproc

# filter parameters
l_freq = 0.1 # high pass
notch_freq = 50  # notch
h_freq = 80  # low pass

freqs = (notch_freq, notch_freq*2, notch_freq*3, notch_freq*4)
raw_filtered = raw.copy().notch_filter(freqs=freqs)
# high pass filter
raw_filtered.filter(
    l_freq=l_freq, h_freq=None, fir_design="firwin", fir_window="hamming"
    )
# low pass filter
raw_filtered.filter(
    l_freq=None, h_freq=h_freq, fir_design="firwin", fir_window="hamming"
    )
# raw_filtered.plot(n_channels=15, duration=2)

# %%
# epoching
events = mne.find_events(
    raw_filtered, stim_channel="STI101", shortest_event=5, min_duration=0.002,initial_event=True
    )
import mne

event_dict = {
    "stand": 12,
    "travIN": 22,
    "travOut": 11,
}

epochs = mne.Epochs(raw_filtered, events, tmin=-1, tmax=3, event_id=event_dict, preload=True)
# epochs["stand"].compute_psd(fmax= 80).plot(picks="meg", exclude="bads")

epochs_decimated = epochs.decimate(2)  # decimate to 500 Hz

# %%
####################
# block for the control group (no feedback)
####################

fig = raw.plot(n_channels=1, duration=2)

# retrieve current selection of bad channels and Annotations
# while the figure window is still open
bads = fig.mne.info['bads']
annotations = fig.mne.inst.annotations

# now we need to know which channels are displayed in the figure
# - using the thread thing ?
# - or using the figure object ? don't know how to do that
# - or pre-define the channels to be displayed, and monitoring the keyboard input all the time to calculate which channel is on the screen
# see below:
# raw.plot()
# order: array of int
# Order in which to plot data.
# If the array is shorter than the number of channels, only the given channels are plotted.
# If None (default), all channels are plotted. If group_by is 'position' or 'selection', the order parameter is used only for selecting the channels to be plotted.


# next problem:
# mne and tkinter are both not thread safe, so we cannot run them in parallel
# - we can use the threading module to run the tkinter window in a separate thread
# - we can use the multiprocessing module to run the mne functions in a separate process
# - we find a thread-safe package for GUI

# then we can use the tkinter window to display the instructions and the buttons

# next, we need to record the user input and compare with the labels

# finally, we need to analyze the results

# %%
####################
# ignore the following code for now
####################

# display text instrcutions
def thread_job():
    print("Thread job started")

def main():
    
    added_thread = threading.Thread(target=thread_job)
    added_thread.start()
    
if __name__ == "__main__":
    main()

# %%
# Create the main window
root = tk.Tk()
# Create a Label widget with the text message
label = tk.Label(root, text="Your text message here")
label.pack()

# Create the "good" and "bad" buttons
good_button = tk.Button(root, text="Good", command=lambda: next_epoch('good'))
bad_button = tk.Button(root, text="Bad", command=lambda: next_epoch('bad'))

# Add the buttons to the window
good_button.pack()
bad_button.pack()

# Current epoch index
current_epoch = 0

# Function to go to the next epoch
def next_epoch(button_clicked):
    global current_epoch
    current_epoch += 1
    # Update the epoch plot
    epochs_decimated["stand"][current_epoch].plot(
        events=events,
        event_id=event_dict,
        n_epochs=1,
        n_channels=1
    )
    # Update the label text
    label.config(text=f"Button {button_clicked} clicked. Now showing epoch {current_epoch}")

# Start the tkinter window in a separate thread
threading.Thread(target=root.mainloop).start()

# Plot the first epoch
epochs_decimated["stand"][current_epoch].plot(
    events=events,
    event_id=event_dict,
    n_epochs=1,
    n_channels=1
)

current_epoch = 1
new_channel = "MEG0111"
epochs_decimated["stand"][current_epoch].plot(
    events=events,
    event_id=event_dict,
    n_epochs=1,
    n_channels=1
    )

# %%
# Function to create and start the tkinter window
def create_tkinter_window():
    root = tk.Tk()
    label = tk.Label(root, text="Your text message here")
    label.pack()
    root.mainloop()

# Start the tkinter window in a separate thread
threading.Thread(target=create_tkinter_window).start()

# Create the main window
root = tk.Tk()
# Create a Label widget with the text message
label = tk.Label(root, text="Your text message here")
label.pack()
# Function to update the tkinter window
def update_tkinter_window(new_text):
    # Update the label text
    label.config(text=new_text)
    # Redraw the window
    root.update()

# Start the tkinter window in a separate thread
threading.Thread(target=root.mainloop).start()

# Now you can update the tkinter window from the main thread
update_tkinter_window("New text message")


# %%
# get user input for good or bad

# %%
# compare with the labels and record the results

# %%
# analyze the results



