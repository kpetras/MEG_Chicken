# %%
# Import packages 
from psychopy import visual, event, core, logging, data, gui
import numpy as np
import mne
import random
import tempfile
import time 
import matplotlib.pyplot as plt
import os
import pandas as pd

# %%
# Load EEG data
path = '/Users/coline/Desktop/Internship/03TPZ5_session2_run01.fif'
raw = mne.io.read_raw_fif(path, preload=True, allow_maxshield=True)

# %%
# Filtering (cutoff frequency in Hz)
lowpass_freq = .5
highpass_freq = 40
raw_filtered = raw.copy().filter(l_freq=lowpass_freq, h_freq=None, fir_design='firwin')
raw_filtered.filter(l_freq=None, h_freq=highpass_freq)

# %%
# Resampling, labelling channels
# Downsample the data 
raw_filtered.resample(250, npad="auto")

# Add channels to the list of "bad datas" 
channels_to_mark_as_bad = ['MEG0332','MEG1022','MEG1143','MEG1242','MEG1333','MEG1433','MEG2013','MEG2023','MEG2413','MEG2623','MEG0121','MEG1931']
raw_filtered.info['bads'].extend(channels_to_mark_as_bad)

# Define channels
all_channels = raw.info['ch_names']
bad_channels = raw.info['bads']
good_channels = [ch for ch in all_channels if ch not in bad_channels]

# %%
# Second block : scroll throught a single channel over time

# Record the results 
filepath = '/Users/coline/Desktop/Internship/data'

dlg = gui.Dlg(title="User Input")
dlg.addField('ParticipantID:')
dlg.addField('Experience: Do you have experience with EEG data? (yes/no)')
ok_data = dlg.show() # display dialog box and wait for user to input data
if dlg.OK: # if user clicks OK
    participantID = ok_data[0]
    experience = ok_data[1]
else: # if user clicks Cancel or closes the dialog box
    core.quit() # exit PsychoPy
filename =(filepath + 'ID' + str(participantID) +  
                        "time" + time.strftime("%Y%m%d-%H%M"))
logFile = logging.LogFile(filename + ".log", level=logging.DEBUG, filemode='w')
logging.console.setLevel(logging.WARNING)

# Create a window
win = visual.Window([1360,750], monitor="testMonitor", units="deg", color='white')

# Create a text stimulus for the instructions
instructions = visual.TextStim(win, text="Welcome in this EEG classification task ! On this first block, EEG channels will be displayed on the screen. Press the right arrow if you think this is a bad channel and press the left arrow if you think this is a good channel. Press [Space bar] to start !", height=1, pos=(0, 0.2), color ='black')

# Draw the instructions and flip the window
instructions.draw()
win.flip()

# Wait for a key press to continue
while not event.getKeys():
    core.wait(0.01)

# Get the sampling rate from the raw object
fs = 250

# Calculate the number of samples in a 2-second segment
number_samples = int(2 * fs)

# Initialize participant_response
participant_response = None

# Loop over 10 iterations
total_trials = 10

for i in range(total_trials):
    # Select a single channel
    selected_channel = random.choice(all_channels)

    # Get the data for the selected channel
    data, times = raw_filtered[selected_channel]

    # Calculate the number of samples in a 2-second segment
    number_samples = int(2 * fs)

    sliding_samples = int(1 * fs)

    # Initialize the start sample
    start_sample = 0

    # Loop until the user presses the escape key
    while True:
        # Select the 2-second segment from the data
        datatimes = data[0, start_sample:start_sample + number_samples]
        times_segment = times[start_sample:start_sample + number_samples]

        # Plot the selected channel
        plt.figure(figsize=(16, 4))
        plt.plot(times_segment, datatimes)
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude (uV)')
        plt.title(f'Timeseries for the channel {selected_channel}')

        # Save the plot as an image in a temporary directory
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp:
            plt.savefig(temp.name)
            temp_image_path = temp.name
        
        # Close the figure
        plt.close()

        # Create an image stimulus
        img = visual.ImageStim(win, image=temp_image_path)

        # Draw the image and flip the window
        img.draw()
        win.flip()
        
        start_time = core.getTime()  # Get the start time

        # Wait for a key press
        while True:
            keys = event.getKeys(keyList=['left', 'right', 'q', 's', 'escape'])
            if 'escape' in keys:  # if escape is pressed
                logging.flush()
                core.rush(False)
                os.rename(filename + ".log", filename + "aborted.log")
                win.close()
                core.quit()
                break 
            elif 'left' in keys:  # if left arrow is pressed 
                # Move to the previous segment
                start_sample = max(0, start_sample - sliding_samples)
                break
            elif 'right' in keys:  # if right arrow is pressed
                # Move to the next segment
                start_sample = min(len(data[0]) - number_samples, start_sample + sliding_samples)
                break
            elif 'q' in keys:  # if 'q' is pressed
                participant_response = 'good'
                response_time = core.getTime() - start_time  # Calculate the response time
                logging.log(level=logging.DATA, msg=f'good, {response_time}')
                break
            elif 's' in keys:  # if 's' is pressed
                participant_response = 'bad'
                response_time = core.getTime() - start_time  # Calculate the response time
                logging.log(level=logging.DATA,  msg=f'bad, {response_time}')
                break
            

        # If a classification was made, break the loop to move to the next channel
        if participant_response is not None:
            break
        
        # Determine if the user's response is correct and provide feedback 
        if (participant_response == "bad" and selected_channel in bad_channels) or (participant_response == "good" and selected_channel in good_channels):
            feedback_text = "Yes, you are right ! [Space bar] to continue."
            feedback_color = 'green'
            logging.log(level=logging.DATA, msg='correct')
        elif (participant_response == "bad" and selected_channel in good_channels) or (participant_response == "good" and selected_channel in bad_channels):
            feedback_text = "No, you are wrong. [Space bar] to continue."
            feedback_color = 'red'
            logging.log(level=logging.DATA, msg='incorrect')
        else:
            feedback_text = "The channel status is not valid."
            feedback_color = 'white'

        # Create a text stimulus for the feedback
        feedback = visual.TextStim(win, text=feedback_text, height=1, color=feedback_color)

        # Draw the feedback and flip the window
        feedback.draw()
        win.flip()

        # Wait for a key press to continue
        while not event.getKeys():
            core.wait(0.01)

# Flush the log messages to the file
logging.flush()

# Check if the log file is not empty
if os.path.getsize(filename + ".log") > 0:
    # Read the log file
    log_data = pd.read_csv(filename + ".log", sep="\t", header=None)

    # Write the data to a CSV file
    log_data.to_csv(filename + ".csv", index=False, sep=",")

    # Read the CSV file into a DataFrame
    df = pd.read_csv(filename + ".csv", delimiter = ",")

    # Print the DataFrame
    print(df)

else:
    print("Log file is empty.")

# Close the window
win.close()
core.quit()