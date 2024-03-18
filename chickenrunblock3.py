# %%
from scipy.io import loadmat
import mne
from mne.preprocessing import ICA
import numpy as np
import matplotlib.pyplot as plt
from psychopy import visual, event, core, logging, data, gui
import os
import tempfile
import time

# Get the path to the home directory
home_dir = os.path.expanduser('~')

# Specify the name of the new directory
new_dir_name = 'my_directory'

# Create the path to the new directory
image_dir = os.path.join(home_dir, new_dir_name)

# Create the new directory
os.makedirs(image_dir, exist_ok=True)

# %%
# Load and label data 

# Load MATLAB file
mat_data = loadmat('/Users/coline/Desktop/datamatlab/SO_02_00_S01_T00_compdat.mat')

# Plot the topoplots of the ICAs components 
# Extract the data and channel names
eeg_data = mat_data['dat'][0,0]['trial'][0,0]/ 1e6 
channel_names = [str(ch[0]) for ch in mat_data['dat'][0,0]['label']]

# Remove extra characters from channel names
channel_names = [name.replace("['", "").replace("']", "") for name in channel_names]

# Define the sample rate
sfreq = mat_data['dat'][0,0]['fsample'][0,0]  # Extract sample rate from the data

# Create the info structure needed by MNE
info = mne.create_info(channel_names, sfreq, ch_types='eeg')

# Create the RawArray object
raw = mne.io.RawArray(eeg_data, info)

# Plot the raw data
raw.plot(n_channels=42, duration=5)

# Define a mapping from channel names to new channel types
channel_types = {
   'Lower VEOG': 'eog', 
   'Upper VEOG': 'eog',
   'Left HEOG': 'eog', 
   'Right HEOG': 'eog', 
   'Offline reference': 'misc'
}

# Set the channel types
raw.set_channel_types(channel_types)

# Set the electrode montage
raw.set_montage('standard_1020')  

# Run ICA with runica method
ica = mne.preprocessing.ICA(n_components=37, method='infomax')
ica.fit(raw)

# Plot components to review and identify artifacts
#ica.plot_components()

# Label the components
# Define the bad components
bad_components = [2, 5, 31]

# Create a dictionary that maps the component indices to their labels
component_labels = {i: 'bad' if i in bad_components else 'good' for i in range(ica.n_components_)}

# %%
# Third block : assess ICAs data along with all the topoplots

# Record the results 
filepath = '/Users/coline/Desktop/Internship/data'

dlg = gui.Dlg(title="User Input")
dlg.addField('ParticipantID:')
dlg.addField('Experience: Do you have experience with ICAs data? (yes/no)')
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

# %%# Create a window
win = visual.Window([900,750], monitor="testMonitor", units="deg", color='white') # Adjust the size as needed

# Create a text stimulus for the instructions
instructions = visual.TextStim(win, text="Welcome in this ICAs topoplots classification task ! On this block, topoplots will be displayed on the screen. We will ask you to identify the bad ones. Look at them carefully and, when you think you identified all the bad ones, press space bar to type your answer. Press [Space bar] to start !", height=1, pos=(0, 0.2), color ='black')

# Draw the instructions and flip the window
instructions.draw()
win.flip()

# Wait for a key press to continue
while not event.getKeys():
    core.wait(0.01)

# Create a list of visual.ImageStim objects for the components
components = []
num_rows = 6  # Adjust as needed
num_cols = 7  # Adjust as needed
size_factor = 2  # Adjust as needed
image_size = (size_factor, size_factor)  # Calculate the size of the images
for i in range(ica.n_components_):
    fig = ica.plot_components(picks=i, show=False)
    image_path = os.path.join(image_dir, f'component_{i}.png')
    fig.savefig(image_path)
    plt.close(fig)
    # Calculate the position of the image on the screen
    x = (i % num_cols - num_cols / 2 + 0.5) * size_factor  # Spread the images across the x-axis
    y = -(i // num_cols - num_rows / 2 + 0.5) * size_factor  # Spread the images across the y-axis
    components.append(visual.ImageStim(win, image=image_path, pos=(x, y), size=image_size))

# Main event loop
while True:
    # Draw the components
    for component in components:
        component.draw()

    # Update the window
    win.flip()

    # Check for space bar press
    keys = event.getKeys()
    if 'space' in keys:
        break

# Create a dialog box for the participant to enter the bad components
dlg = gui.Dlg(title="Bad Components")
dlg.addField('Enter the numbers of the bad components, separated by commas:')
ok_data = dlg.show()  # show dialog and wait for OK or Cancel
if dlg.OK:  # or if ok_data is not None
    participant_bad_components = [int(num) for num in ok_data[0].split(',')]  # Convert the input to a list of integers
else:
    print('User cancelled.')

# Compare the participant's input with the actual bad components and provide feedback
feedback = visual.TextStim(win, text='', color='black')
correct_answers = set(participant_bad_components) & set(bad_components)
incorrect_answers = set(participant_bad_components) - set(bad_components)
missed_answers = set(bad_components) - set(participant_bad_components)

# Log the results
logging.info(f'Number of correct answers: {len(correct_answers)}')
logging.info(f'Number of incorrect answers: {len(incorrect_answers)}')
logging.info(f'Number of missed answers: {len(missed_answers)}')

if correct_answers and not incorrect_answers and not missed_answers:
    feedback.text = f'Correct, these are the bad components you identified correctly: {correct_answers}'
elif correct_answers:
    feedback.text = f'Partially correct, these are the bad components you identified correctly: {correct_answers}. These are the ones you missed: {missed_answers}. These are the incorrect ones: {incorrect_answers}'
else:
    feedback.text = f'You did not identify any bad components correctly. These are the ones you missed: {missed_answers}. These are the incorrect ones: {incorrect_answers}'
feedback.draw()
win.flip()

# Wait for a space press before closing the window
while True:
    if 'space' in event.getKeys():
        break
    core.wait(0.1)

# New task : assess ICAs data with topoplots one by one

# Select 5 random components
selected_components = random.sample(components, 5)

# Iterate over the components
for i, component in enumerate(selected_components):
    # Display the component
    component.draw()
    win.flip()

    # Wait for a key press
    while True:
        keys = event.getKeys()
        if 'left' in keys:
            participant_response = 'good'
            break
        elif 'right' in keys:
            participant_response = 'bad'
            break
        core.wait(0.1)

    # Check the participant's response and provide feedback
    if (i in bad_components and participant_response == 'bad') or (i not in bad_components and participant_response == 'good'):
        feedback.text = 'Correct'
    else:
        feedback.text = 'Incorrect'
    feedback.draw()
    win.flip()
    core.wait(2)  # Wait for 2 seconds before moving to the next component

# Wait for a space press before closing the window
while True:
    if 'space' in event.getKeys():
        break
    core.wait(0.1)

win.close()