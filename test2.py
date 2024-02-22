# %%
# Import packages 
import mne
import random 
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# First block : assess a single channel 

# Function to handle button clicks 
# Give a feedback according to the channel status and the button clicked, record the results and display the next channel
def classify_channel(status):
    global selected_channel, classification_results
    if (status == "bad" and selected_channel in bad_channels) or (status == "good" and selected_channel in good_channels):
        feedback_label.config(text="Yes, you are right!", foreground="green", font=("Helvetica", 16, "bold"))
        classification_results.append(1)
    elif (status == "bad" and selected_channel in good_channels) or (status == "good" and selected_channel in bad_channels):
        feedback_label.config(text="No, you are wrong.", foreground="red", font=("Helvetica", 16, "bold"))
        classification_results.append(0)
    else:
        feedback_label.config(text="The channel status is not valid.")
    next_channel()

# Function to display the first channel
# To display the first channel before the user starts the classification
def first_channel():
    global selected_channel
    selected_channel = random.choice(all_channels)
    channel_label.config(text=f"Selected channel: {selected_channel}")
    data, times = raw[selected_channel]
    datatimes = data[0, 2000:4000]
    times = times[2000:4000]
    ax.clear()
    ax.plot(times, datatimes)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Amplitude (uV)')
    ax.set_title(f'Timeseries for the channel {selected_channel}')
    canvas.draw()

# Function to display the next channel until the current channel index reaches the number of loops
def next_channel():
    global selected_channels, current_channel_index
    if current_channel_index < len(selected_channels):
        selected_channel = selected_channels[current_channel_index]
        channel_label.config(text=f"Selected channel: {selected_channel}")
        data, times = raw[selected_channel]
        datatimes = data[0, 2000:4000]
        times = times[2000:4000]
        ax.clear()
        ax.plot(times, datatimes)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Amplitude (uV)')
        ax.set_title(f'Timeseries for the channel {selected_channel}')
        canvas.draw()
        current_channel_index += 1

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

# Initialize variables
# Create a list of random selected channels that lenght is equal to the number of loops
# Create a list to store the classification results
# Initialize the current channel index to 0
number_loops = 10
selected_channels = random.sample(all_channels, number_loops)
classification_results = []
current_channel_index = 0

# GUI setup
# Create a GUI window
root = tk.Tk()
root.title("EEG Channel Classification")

# Create GUI elements
channel_label = ttk.Label(root, text="")
channel_label.pack()

# Create a figure and a canvas to display the EEG data
fig, ax = plt.subplots(figsize=(8, 4))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
toolbar = NavigationToolbar2Tk(canvas, root)
toolbar.update()
canvas.draw()

# Display the first channel before to click on the buttons
first_channel()

# Create a label to display the feedback
feedback_label = ttk.Label(root, text="")
feedback_label.pack()

# Create a frame to hold the buttons
button_frame = ttk.Frame(root)
button_frame.pack()

# Create buttons to classify the channel
good_button = ttk.Button(button_frame, text="Good", command=lambda: classify_channel("good"))
good_button.pack(side=tk.LEFT, padx=10)

bad_button = ttk.Button(button_frame, text="Bad", command=lambda: classify_channel("bad"))
bad_button.pack(side=tk.LEFT, padx=10)

# Start the GUI main loop
root.mainloop()

# Print the classification results
print("Classification results for the first block:", classification_results)
