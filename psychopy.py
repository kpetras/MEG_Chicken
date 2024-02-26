# %%
# Import packages 
from psychopy import visual, event, core
import matplotlib.pyplot as plt
import numpy as np
import mne
import random
import tempfile

# %%
# Load, downsample the data and label channels
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

# %%
# First block : assess a single channel 

# Record the results 
classification_results = []

# Select a random channel
selected_channel = random.choice(all_channels)

# Get the data for the selected channel
data, times = raw[selected_channel]

# Select a specific time range from the data
datatimes = data[0, 2000:4000]
times = times[2000:4000]

# Plot the seleted channel
plt.figure(figsize=(8, 4))
plt.plot(times, datatimes)
plt.xlabel('Time (s)')
plt.ylabel('Amplitude (uV)')
plt.title(f'Timeseries for the channel {selected_channel}')

# Save the plot as an image in a temporary directory
with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp:
    plt.savefig(temp.name)
    temp_image_path = temp.name

# Create a window
win = visual.Window([800,600], monitor="testMonitor", units="deg")

# Create a text stimulus for the instructions
instructions = visual.TextStim(win, text="Welcome in this EEG classification task ! EEG channels will be displayed on the screen. Press right arrow if you think it is a bad channel and left arrow for a good channel.", height=1)

# Draw the instructions and flip the window
instructions.draw()
win.flip()

# Wait for a key press to continue
while not event.getKeys():
    core.wait(0.01)

# Create an image stimulus
img = visual.ImageStim(win, image=temp_image_path)

# Draw the image and flip the window
img.draw()
win.flip()

# Wait for a key press
while True:
    keys = event.getKeys(keyList=['left', 'right'])
    if 'left' in keys:  # if left arrow is pressed
        channel_status = 'good'
        break
    elif 'right' in keys:  # if right arrow is pressed
        channel_status = 'bad'
        break
    core.wait(0.01)

# Determine if the user's response is correct and provide feedback 
if (channel_status == "bad" and selected_channel in bad_channels) or (channel_status == "good" and selected_channel in good_channels):
    feedback_text = "Yes, you are right!"
    classification_results.append(1)
elif (channel_status == "bad" and selected_channel in good_channels) or (channel_status == "good" and selected_channel in bad_channels):
    feedback_text = "No, you are wrong."
    classification_results.append(0)
else:
    feedback_text = "The channel status is not valid."

# Create a text stimulus for the feedback
feedback = visual.TextStim(win, text=feedback_text, height=1)

# Draw the feedback and flip the window
feedback.draw()
win.flip()

# Wait for a key press to continue
while not event.getKeys():
    core.wait(0.01)

# Close the window
win.close()

print(classification_results)
# %%
