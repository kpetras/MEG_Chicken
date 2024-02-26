# Import packages 
from psychopy import visual, core
import matplotlib.pyplot as plt
import numpy as np
import mne
import random
import tempfile

# Load EEG data
path = '/Users/coline/Desktop/Internship/03TPZ5_session2_run01.fif'
raw = mne.io.read_raw_fif(path, preload=True, allow_maxshield=True)

# Downsample the data 
raw_resampled = raw.copy().resample(250, npad="auto")

# Add channels to the list of "bad datas" 
channels_to_mark_as_bad = ['MEG0332','MEG1022','MEG1143','MEG1242','MEG1333','MEG1433','MEG2013','MEG2023','MEG2413','MEG2623','MEG0121','MEG1931']
raw_resampled.info['bads'].extend(channels_to_mark_as_bad)

# Define channels
all_channels = raw.info['ch_names']
bad_channels = raw.info['bads']
good_channels = [ch for ch in all_channels if ch not in bad_channels]

# First block : assess a single channel 
classification_results = []

# Select a random channel
selected_channel = random.choice(all_channels)

# Get the data for the selected channel
data, times = raw[selected_channel]

# Select a specific time range from the data
data = data[0, 2000:4000]
times = times[2000:4000]

# Plot the data
plt.plot(times, data.T)
plt.xlabel('Time (s)')
plt.ylabel('Amplitude (uV)')
plt.title(f'Timeseries for the channel {selected_channel}')

# Save the plot as an image in a temporary directory
with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp:
    plt.savefig(temp.name)
    temp_image_path = temp.name

# Create a window
win = visual.Window([800,600], monitor="testMonitor", units="deg")

# Create an image stimulus
img = visual.ImageStim(win, image=temp_image_path)

# Draw the image
img.draw()

# Flip the window
win.flip()

# Keep the window open for 5 seconds
core.wait(5)

# Close the window
win.close()