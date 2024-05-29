# chickenrun_exp.py

####################
# block for the experimental group (with feedback)
####################

# %%
# Import packages
import numpy as np
import mne
import tkinter as tk
import threading
import time
from pynput import keyboard
import HelperFuns as hf
import os
import mne
from threading import Thread
from pynput import keyboard
import time
from PyQt5.QtWidgets import QApplication
import random
import tkinter as tk
from tkinter import messagebox
import pickle
import csv
from slides import display_slides

def show_instructions():
    instructions1 = "Welcome in this EEG and MEG data classification experiment ! EEG and MEG recordings will be displayed on the screen. If you think a channel is contaminated by artifacts, you can click on it."
    instructions2 = "You can select multiple channels or no channel at all. To validate your answer and display the next trial, you can press TAB. Good luck !"
    messagebox.showinfo("Instructions - Page 1", instructions1)
    messagebox.showinfo("Instructions - Page 2", instructions2)

def on_press(key):
    if key == keyboard.Key.space:
        shared['space_pressed'] = True        
    if key == keyboard.Key.tab:
        shared['tab_pressed'] = True

def create_label_entry(window, text, row):
    label = tk.Label(window, text=text)
    label.grid(row=row, column=0)
    entry = tk.Entry(window)
    entry.grid(row=row, column=1)
    return entry

def submit():
    global participantNumber, experienceLevel, SessionNumber
    participantNumber = entry1.get()
    experienceLevel = entry2.get()
    SessionNumber = entry3.get()

    # Check if experience level is between 1 and 4
    if not experienceLevel.isdigit() or int(experienceLevel) < 1 or int(experienceLevel) > 4:
        messagebox.showerror("Invalid input", "Experience level must be a number between 1 and 4")
        return
    
    # Call the function to display the instructions before starting the task
    show_instructions()

    # Close the window after the inputs are saved
    window.destroy()

participantNumber = None
experienceLevel = None
SessionNumber = None
window = tk.Tk()
entry1 = create_label_entry(window, "Participant Number", 0)
entry2 = create_label_entry(window, "Experience Level, from very experienced to fully naïve (1-4)", 1)
entry3 = create_label_entry(window, "Session Number", 2)
submit_button = tk.Button(window, text="Submit", command=submit)
submit_button.grid(row=3, column=0, columnspan=2)

# Start the GUI event loop
window.mainloop()

# Display the slides
slide_folder = r'slides'
display_slides(slide_folder)

dataPath = 'trial_data\\'  
fileList = os.listdir(dataPath)
# Get the trial data
nTrial = 5
filePath = np.random.choice(fileList, nTrial, replace=False)

results = []
#start the loop over trials
count=1
for trial in range(nTrial):
    #load the data
    with open(dataPath + filePath[trial], 'rb') as f:
        pairedData = pickle.load(f)
    print('processing file: ', filePath[trial])
    trialData = pairedData[0]
    badChansInDisplay = pairedData[1]
    n_channels = pairedData[0].get_data().shape[0] #number of chans in display
    # open interactive window
    fig = trialData.plot(n_channels=n_channels, duration=2, block=False)
    print("trialNr:" + str(count))
    # Initialize previous_bads to an empty list
    previous_bads = []
    # Create a shared dictionary
    shared = {'space_pressed': False,
                'tab_pressed': False,
                'done': False,
                'hits': 0,
                'false_alarms': 0,
                'misses': 0,
                'correct_rejections': n_channels}

    # Create a new thread that runs the monitor_bads_no_feedback function
    thread = Thread(target=hf.monitor_bads_no_feedback, args=(fig, badChansInDisplay, shared))

    # Start the new thread
    thread.start()

    # Start listening for key press
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    # Wait for the thread to finish
    while not shared['done']:
        # Process the GUI event loop
        QApplication.processEvents()
        # Sleep for a short time to reduce CPU usage
        time.sleep(0.1)    

    # Collect results into a dictionary and append to results list
    trial_results = {
        'hits': shared.get('hits'),
        'false_alarms': shared.get('false_alarms'),
        'misses': shared.get('misses'),
        'correct_rejections': shared.get('correct_rejections')
    }
    results.append(trial_results)
    count+=1

# Save results
filename = f'results_participant_{participantNumber}_session_{SessionNumber}_experience_{experienceLevel}.csv'
results_path = os.path.join('experimental', 'channel_results', filename)
with open(results_path, 'w', newline='') as f:
    writer = csv.writer(f)
    # Write the header
    writer.writerow(['trial', 'hits', 'false_alarms', 'misses', 'correct_rejections'])
    # Write the results
    for i, trial_results in enumerate(results, start=1):
        writer.writerow([i, trial_results['hits'], trial_results['false_alarms'], trial_results['misses'], trial_results['correct_rejections']])

# Save the file list used in the experiment
filelist_filename = 'files_' + filename
filelist_path = os.path.join('experimental', 'channel_results', filelist_filename)
with open(filelist_path, 'w') as f:
    for item in filePath:
        f.write("%s\n" % item)
#%%



