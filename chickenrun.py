# %%
# Import packages 
from psychopy import visual, event, core, logging, data, gui
import numpy as np
import mne
import random
import tempfile
import time 
import matplotlib.pyplot as plt

# Load the data
datapath = '/Users/coline/Desktop/Internship/tempfile.fif'
raw = mne.io.read_raw_fif(datapath, preload=True, allow_maxshield=True)

# Define channels
all_channels = raw.info['ch_names']
bad_channels = raw.info['bads']
good_channels = [ch for ch in all_channels if ch not in bad_channels]

# %%
# First block : assess a single channel 
# Record the results 
filepath = '/Users/coline/Desktop/Internship/data'
classification_results = []

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
win = visual.Window([800,600], monitor="testMonitor", units="deg", color='white')

# Create a text stimulus for the instructions
instructions = visual.TextStim(win, text="Welcome in this EEG classification task ! On this first block, EEG channels will be displayed on the screen. Press the right arrow if you think this is a bad channel and press the left arrow if you think this is a good channel. Press [Space bar] to start !", height=1, pos=(0, 0.2), color ='black')

# Draw the instructions and flip the window
instructions.draw()
win.flip()

# Wait for a key press to continue
while not event.getKeys():
    core.wait(0.01)

# Loop over 10 iterations
for i in range(10):
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
        keys = event.getKeys(keyList=['left', 'right', 'escape'])
        if 'escape' in keys:  # if escape is pressed
            logging.flush()
            win.close()
            core.quit()
            sys.exit()
            break 
        elif 'left' in keys:  # if left arrow is pressed 
            participant_response = 'good'
            response_time = core.getTime() - start_time  # Calculate the response time
            logging.log(level=logging.DATA, msg=f'good, {response_time}')
            break
        elif 'right' in keys:  # if right arrow is pressed
            participant_response = 'bad'
            response_time = core.getTime() - start_time  # Calculate the response time
            logging.log(level=logging.DATA,  msg=f'bad, {response_time}')
            break
        core.wait(0.01)

    # Determine if the user's response is correct and provide feedback 
    if (participant_response == "bad" and selected_channel in bad_channels) or (participant_response == "good" and selected_channel in good_channels):
        feedback_text = "Yes, you are right ! [Space bar] to continue."
        feedback_color = 'green'
        classification_results.append(1)
        logging.log(level=logging.DATA, msg='correct')
    elif (participant_response == "bad" and selected_channel in good_channels) or (participant_response == "good" and selected_channel in bad_channels):
        feedback_text = "No, you are wrong. [Space bar] to continue."
        feedback_color = 'red'
        classification_results.append(0)
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

# Close the window
win.close()
core.quit()

print(classification_results)

# %%
