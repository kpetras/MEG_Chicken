# %%
import mne
import random 
import numpy as np
import matplotlib.pyplot as plt

# %%
# Load EEG data
raw = mne.io.read_raw_fif('03TPZ5_session2_run01.fif', preload=True, allow_maxshield=True)
print(raw.info)

# %%
# Downsample the data 
raw_resampled = raw.copy().resample(250, npad="auto")
print(raw_resampled.info)

# %%
# Add channels to the list of "bad datas" 
channels_to_mark_as_bad = ['MEG0332','MEG1022','MEG1143','MEG1242','MEG1333','MEG1433','MEG2013','MEG2023','MEG2413','MEG2623','MEG0121','MEG1931']
raw_resampled.info['bads'].extend(channels_to_mark_as_bad)
print(raw_resampled.info)

# %%
# Define channels
all_channels = raw.info['ch_names']
bad_channels = raw.info['bads']
good_channels = [ch for ch in all_channels if ch not in bad_channels]

# %%
# Select a random channel
selected_channel = random.choice(all_channels)
print("Selected channel:", selected_channel)

# %%
# Plot the selected channel 
data, times = raw[selected_channel]
datatimes = data[0,2000:4000]
times = times[2000:4000]
plt.figure(figsize=(10, 4))
plt.plot(times, datatimes)
plt.xlabel('Time (s)')
plt.ylabel('Amplitude (uV)')
plt.title(f'Timeseries for the channel {selected_channel}')
plt.show()

# %%
# Ask the user to classify the channel as "good" or "bad"
channel_status = input("Is it a good or a bad channel ?")

# %%
# Determine if the user's response is correct and provide feedback 
if (channel_status == "bad" and selected_channel in bad_channels) or (channel_status == "good" and selected_channel in good_channels):
    print("Yes, you are right!")
elif (channel_status == "bad" and selected_channel in good_channels) or (channel_status == "good" and selected_channel in bad_channels):
    print("No, you are wrong.")
else:
    print("The channel status is not valid.")

