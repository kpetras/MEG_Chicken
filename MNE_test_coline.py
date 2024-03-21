#%%
import numpy as np
import mne
import random
import tempfile
import time 
import matplotlib.pyplot as plt
import os
import pandas as pd
from mne.io import RawArray
import threading
import time
import tkinter as tk
from tkinter import messagebox

# %%
def add_arrows(axes):
    # add some arrows at 60 Hz and its harmonics
    for ax in axes:
        freqs = ax.lines[-1].get_xdata()
        psds = ax.lines[-1].get_ydata()
        for freq in (50, 100, 150, 200):
            idx = np.searchsorted(freqs, freq)
            # get ymax of a small region around the freq. of interest
            y = psds[(idx - 4) : (idx + 5)].max()
            ax.arrow(
                x=freqs[idx],
                y=y + 18,
                dx=0,
                dy=-12,
                color="red",
                width=0.1,
                head_width=3,
                length_includes_head=True,
            )

#%% Load the data
folder  = '/Users/coline/Desktop/Internship/'
basename = '03TPZ5_session2_run01.fif'
datapath = folder + basename
raw = mne.io.read_raw_fif(datapath, preload=True, allow_maxshield=True)

# %% test Coline

# Our list of bad channels
bad_channels_list = ['MEG0212','MEG0213','MEG0222','MEG0223']  # replace with our list of bad channels

class ObservableRaw(RawArray):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stop_thread = False

    def set_channel_types(self, mapping):
        print("set_channel_types has been called")
        super().set_channel_types(mapping)

    def set_eeg_reference(self, ref_channels, projection=False, ch_type='auto', verbose=None):
        print("set_eeg_reference has been called")
        super().set_eeg_reference(ref_channels, projection, ch_type, verbose)

# Usage
raw = ObservableRaw(raw._data, raw.info)  # replace raw._data and raw.info with your raw object's data and info

# Run a separate thread to check for updates
def check_updates():
    while not raw.stop_thread:
        if raw.info['bads'] and raw.info['bads'][-1] in bad_channels_list:
            print("Match found: ", raw.info['bads'][-1])
            root = tk.Tk()
            root.withdraw()  # hide the main window
            messagebox.showinfo("Good job!", "Match found: " + raw.info['bads'][-1])
            root.destroy()  # destroy the main window
        else:
            print("No match found")
        time.sleep(1)  # wait for 1 second

thread = threading.Thread(target=check_updates)
thread.start()

info = raw.plot(n_channels=15, duration=2)

# When you want to stop the thread
raw.stop_thread = True

#%%

raw.plot(n_channels=15, duration=2)
ok_data = dlg.show() # display dialog box and wait for user to input data
if dlg.OK: # if user clicks OK
    bad_channels = ok_data[0].split(',')
    bad_channels = [int(i) for i in bad_channels]
    raw.info['bads'] = bad_channels
l_freq = 0.1  # high pass frequency
notch_freq = 50  # notch frequency
h_freq = 80  # low pass frequency

# meg_picks = mne.pick_types(raw.info, meg=True)
freqs = (notch_freq, notch_freq*2, notch_freq*3, notch_freq*4)
raw_filtered = raw.copy().notch_filter(freqs=freqs) #, picks=meg_picks)

# high pass filter
raw_filtered.filter(
    l_freq=l_freq, h_freq=None, fir_design="firwin", fir_window="hamming"
    )
# low pass filter
raw_filtered.filter(
    l_freq=None, h_freq=h_freq, fir_design="firwin", fir_window="hamming"
    )
raw_filtered.plot(n_channels=15, duration=2)
# visualize filter
filter_params = mne.filter.create_filter(
    raw.get_data(), raw.info["sfreq"], l_freq=l_freq, h_freq=h_freq
)
#mne.viz.plot_filter(filter_params, raw.info["sfreq"], flim=(0.01, 150))


# plot PSD before and after filtering
for title, data in zip(["Un", "After "], [raw, raw_filtered]):
    fig = data.compute_psd(fmax=250).plot(average=True, picks="data", exclude="bads")
    fig.suptitle("{}filtered".format(title), size="xx-large", weight="bold")
    add_arrows(fig.axes[:2])
    
raw_filtered.save(folder+ basename + '_preproc.fif', overwrite=True)
events = mne.find_events(
    raw_filtered, stim_channel="STI101", shortest_event=5, min_duration=0.002,initial_event=True
    )
#print(events)  # show the first 5

event_dict = {
    "stand": 12,
    "travIN": 22,
    "travOut": 11,
}

epochs = mne.Epochs(raw_filtered, events, tmin=-1, tmax=3, event_id=event_dict, preload=True)
epochs["stand"].plot(
    events=events,
    event_id=event_dict,
)
epochs["stand"].compute_psd(fmax= 80).plot(picks="meg", exclude="bads")

epochs_decimated = epochs.decimate(2)  # decimate to 500 Hz

# %%
epochs_decimated["stand"].plot(
    events=events,
    event_id=event_dict,
    n_epochs = 1,
    n_channels = 15
)

#%%