# %%
from scipy.io import loadmat
import mne
from mne.preprocessing import ICA
import numpy as np
import matplotlib.pyplot as plt
from psychopy import visual, event, core, data, gui
import os
import tempfile

# Get the path to the home directory
home_dir = os.path.expanduser('~')

# Specify the name of the new directory
new_dir_name = 'my_directory'

# Create the path to the new directory
image_dir = os.path.join(home_dir, new_dir_name)

# Create the new directory
os.makedirs(image_dir, exist_ok=True)

# %%
# Load MATLAB file
mat_data = loadmat('/Users/coline/Desktop/datamatlab/SO_02_00_S01_T00_compdat.mat')

# %%
# Third block : assess ICAs data along topoplots

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
# %%
# Label the components
# Define the bad components
bad_components = [2, 5, 31]

# Create a dictionary that maps the component indices to their labels
component_labels = {i: 'bad' if i in bad_components else 'good' for i in range(ica.n_components_)}

# %%
# Create a window
win = visual.Window([900,750], monitor="testMonitor", units="deg", color='white') # Adjust the size as needed

# Create a mouse object
mouse = event.Mouse(win=win)

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

    # Check for mouse clicks
    if mouse.getPressed()[0]:  # If the left mouse button is pressed
        # Get the position of the mouse
        mouse_pos = mouse.getPos()

        # Determine which component was clicked on
        clicked_component = None
        for i, component in enumerate(components):
            if component.contains(mouse_pos):
                clicked_component = i
                break

    # Check for space bar press
    keys = event.getKeys()
    if 'space' in keys:
        break

# If a component was clicked on, provide feedback
if clicked_component is not None:
    feedback = visual.TextStim(win, text='', color='black')
    if clicked_component in bad_components:
        feedback.text = 'Correct, this is a bad component.'
    else:
        feedback.text = 'Incorrect, this is a good component.'
    feedback.draw()
    win.flip()
    core.wait(2)  # Wait for 2 seconds before closing the window

win.close()