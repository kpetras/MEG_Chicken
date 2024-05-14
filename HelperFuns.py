# HelperFuns.py

import tkinter as tk
import time
import threading
from pynput import keyboard
import csv
import mne
import os

def display_message(message, color):
    """Displays a temporary window with a message."""
    # Create a new Tk root
    root = tk.Tk()

    # Hide the root window drag bar and close button
    root.overrideredirect(True)
    root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))

    # Make the root window always on top
    root.attributes('-topmost', True)

    # Create a label with the message
    label = tk.Label(root, text=message, fg=color, bg='black',
                     font=('Helvetica', 72), padx=root.winfo_screenwidth() // 2,
                     pady=root.winfo_screenheight() // 2)

    # Add the label to the root
    label.pack()

    # Update the GUI
    root.update()

    # Pause for 1 second
    time.sleep(1)

    # Destroy the root
    root.destroy()


def monitor_bads(fig, badChansInDisplay, shared):
    """Monitors bad channels, provides feedback, and stores results."""

    # Initialize previous_bads to an empty list
    previous_bads = []
    
    # Initialize a counter
    counter = 0

    # Track responses
    hits = 0
    false_alarms = 0
    correct_rejections = 0

    # Create a keyboard controller
    controller = keyboard.Controller()

    try:
        print("start loop")

        while True:
            # Get the current bads
            current_bads = fig.mne.info['bads']
            # Check if the space key has been pressed
            if shared.get('space_pressed', False):
                print("Space key pressed.")
                shared['space_pressed'] = False
                
                answer_set = set(badChansInDisplay)
                current_bads_set = set(current_bads)

                # New : Trouver les channels manquants en comparant les deux ensembles
                missing_channels = answer_set - current_bads_set

                if missing_channels:
                    print(f"Missing channels: {', '.join(missing_channels)}")
                else:
                    print("All bad channels were correctly identified.")
                
            # print("Current bads: ", current_bads)  # Check if current_bads is updating

            # Check if the length has changed
            if len(current_bads) != len(previous_bads):
                # print("Length of bads has changed.")

                # Find which elements were added
                added = set(current_bads) - set(previous_bads)
                if added:
                    print("Added: ", added)
                    # check if added is in the answer
                    added_in_answer = [item for item in added if item in badChansInDisplay]

                    if added_in_answer:
                        print("Correctly added: ", added_in_answer)
                        hits += len(added_in_answer)
                        display_message("Good Job!", "green")

                    else:
                        print("Incorrectly added: ", added)
                        false_alarms += len(added)
                        display_message("Incorrect! Try again", "red")

                # Find which elements were removed
                removed = set(previous_bads) - set(current_bads)
                if removed:
                    print("Removed: ", removed)
                    # check if removed is in the answer
                    removed_in_answer = [item for item in removed if item not in badChansInDisplay]
                    if removed_in_answer:
                        print("Correctly removed: ", removed_in_answer)
                    else:
                        print("Incorrectly removed: ", removed)

            # Update previous_bads
            previous_bads = current_bads.copy()

            # Increment the counter
            counter += 1

            # Check if the Tab key has been pressed
            if shared.get('tab_pressed', False):
                print("Tab key pressed.")
                shared['tab_pressed'] = False
                shared['done'] = True
                # Simulate Escape key press to close the figure
                controller.press(keyboard.Key.esc)
                controller.release(keyboard.Key.esc)                
                break
            # if counter >= 100:
            #     break

            # Wait for a short period of time before checking again
            time.sleep(1)
            
        print("end loop")        
        
    except Exception as e:
        print("Error in thread: ", e)  # Check if there's an error in the thread
    
    misses = len(set(badChansInDisplay) - set(previous_bads))
    correct_rejections = - hits - false_alarms - misses

    # Store the output in the shared dict
    shared['hits'] = hits
    shared['false_alarms'] = false_alarms
    shared['misses'] = misses
    shared['correct_rejections'] += correct_rejections


def monitor_ICs(ica, answer, shared):
    """Monitors bad ICs, provides feedback, and stores results."""

    # Initialize previous_bads to an empty list
    previous_bads = []
    
    # Initialize a counter
    counter = 0

    # Track responses
    hits = 0
    false_alarms = 0
    
    # Create a keyboard controller
    controller = keyboard.Controller()

    try:
        print("start loop")

        while True:
            # Get the current bads
            current_bads = ica.exclude
            # Check if the space key has been pressed
            if shared.get('space_pressed', False):
                print("Space key pressed.")
                shared['space_pressed']= False
                
                answer_set = set(answer)
                current_bads_set = set(current_bads)

                # New : Trouver les channels manquants en comparant les deux ensembles
                missing_ICs = answer_set - current_bads_set

                if missing_ICs:
                    print(f"Missing ICs: {', '.join(map(str, missing_ICs))}")
                else:
                    print("All bad ICs were correctly identified.")

            # print("Current bads: ", current_bads)  # Check if current_bads is updating

            # Check if the length has changed
            if len(current_bads) != len(previous_bads):
                # print("Length of bads has changed.")

                # Find which elements were added
                added = set(current_bads) - set(previous_bads)
                if added:
                    print("Added: ", added)
                    # check if added is in the answer
                    added_in_answer = [item for item in added if item in answer]

                    if added_in_answer:
                        print("Correctly added: ", added_in_answer)
                        hits += len(added_in_answer)
                        print(hits)
                        display_message("Good Job!", "green")
                    else:
                        print("Incorrectly added: ", added)
                        false_alarms += len(added)
                        display_message("Incorrect! Try again", "red")

                # Find which elements were removed
                removed = set(previous_bads) - set(current_bads)
                if removed:
                    print("Removed: ", removed)
                    # check if removed is in the answer
                    removed_in_answer = [item for item in removed if item not in answer]
                    if removed_in_answer:
                        print("Correctly removed: ", removed_in_answer)
                    else:
                        print("Incorrectly removed: ", removed)

            # Update previous_bads
            previous_bads = current_bads.copy()

            # Increment the counter
            counter += 1

            # Check if the Tab key has been pressed
            if shared.get('tab_pressed', False):
                print("Tab key pressed.")
                shared['tab_pressed']= False
                shared['done'] = True
                # Simulate Escape key press to close the figure 
                controller.press(keyboard.Key.esc)
                controller.release(keyboard.Key.esc)
                break

            # # Break the loop after 20 iterations
            # if counter >= 20:
            #     break

            # Wait for a short period of time before checking again
            time.sleep(1)
            
        print("end loop")
        
    except Exception as e:
        print("Error in thread: ", e)  # Check if there's an error in the thread
    
    misses = len(set(answer) - set(previous_bads))
    correct_rejections = - hits - false_alarms - misses

    # Store the output in the shared dict
    shared['hits'] = hits
    shared['false_alarms'] = false_alarms
    shared['misses'] = misses
    shared['correct_rejections'] += correct_rejections


def monitor_bads_no_feedback(fig, badChansInDisplay, shared):
    """Monitors bad channels without feedback and stores results."""

    previous_bads = []
    counter = 0
    hits = 0
    false_alarms = 0
    correct_rejections = 0
    misses = 0 
    controller = keyboard.Controller()

    try:
        while True:
            current_bads = fig.mne.info['bads']

            if shared.get('space_pressed', False):
                shared['space_pressed'] = False

            if len(current_bads) != len(previous_bads):
                added = set(current_bads) - set(previous_bads)
                hits += len([item for item in added if item in badChansInDisplay])
                false_alarms += len([item for item in added if item not in badChansInDisplay])

                removed = set(previous_bads) - set(current_bads)
                misses += len([item for item in removed if item in badChansInDisplay])

            previous_bads = current_bads.copy()
            counter += 1

            if shared.get('tab_pressed', False):
                shared['tab_pressed'] = False
                shared['done'] = True
                controller.press(keyboard.Key.esc)
                controller.release(keyboard.Key.esc)
                break

            time.sleep(1)

        misses = len(set(badChansInDisplay) - set(previous_bads))
        correct_rejections = -hits - false_alarms - misses

        shared['hits'] = hits
        shared['false_alarms'] = false_alarms
        shared['misses'] = misses
        shared['correct_rejections'] += correct_rejections

    except Exception as e:
        print("Error in thread: ", e)


def monitor_ICs_no_feedback(ica, answer, shared):
    """Monitors bad ICs without feedback and stores results."""

    previous_bads = []
    counter = 0
    hits = 0
    false_alarms = 0
    misses = 0 
    controller = keyboard.Controller()

    try:
        while True:
            current_bads = ica.exclude

            if shared.get('space_pressed', False):
                shared['space_pressed'] = False

            if len(current_bads) != len(previous_bads):
                added = set(current_bads) - set(previous_bads)
                hits += len([item for item in added if item in answer])
                false_alarms += len([item for item in added if item not in answer])

                removed = set(previous_bads) - set(current_bads)
                misses += len([item for item in removed if item in answer])

            previous_bads = current_bads.copy()
            counter += 1

            if shared.get('tab_pressed', False):
                shared['tab_pressed'] = False
                shared['done'] = True
                controller.press(keyboard.Key.esc)
                controller.release(keyboard.Key.esc)
                break

            time.sleep(1)

        misses = len(set(answer) - set(previous_bads))
        correct_rejections = -hits - false_alarms - misses

        shared['hits'] = hits
        shared['false_alarms'] = false_alarms
        shared['misses'] = misses
        shared['correct_rejections'] += correct_rejections
    
    except Exception as e:
        print("Error in thread: ", e)


def save_results_bads(subj, ses, run, hits, false_alarms, misses, correct_rejections, group):
    """Saves the results of monitor_bads to a CSV file."""
    directory = os.path.join(group, "bads_results")
    os.makedirs(directory, exist_ok=True)
    results_path = os.path.join(directory, f"{subj}_{ses}_{run}_bads_results.csv")
 
    with open(results_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Hits", "False Alarms", "Misses", "Correct Rejections"])
        writer.writerow([hits, false_alarms, misses, correct_rejections])
    
    print(f"Results saved to: {results_path}")


def save_results_ICs(subj, ses, run, hits, false_alarms, misses, correct_rejections, group):
    """Saves the results of monitor_ICs to a CSV file."""
    directory = os.path.join(group, "ICs_results")
    os.makedirs(directory, exist_ok=True)
    results_path = os.path.join(directory, f"{subj}_{ses}_{run}_ICs_results.csv")

    with open(results_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Hits", "False Alarms", "Misses", "Correct Rejections"])
        writer.writerow([hits, false_alarms, misses, correct_rejections])
    
    print(f"Results saved to: {results_path}")


def load_preprocessed_data(data_path): 
    """ 
    Loads preprocessed data from a specified directory. 
    
    Args: 
        data_path (str): full path to preprocessed files. 

    Returns: 
        mne.io.Raw: Preprocessed raw data. 
    """ 
    fname = f"{data_path}_preprocessed-raw.fif" 
    fname_with_path = f"{data_path}{fname}" 
    
    return mne.io.read_raw_fif(fname_with_path, preload=True, allow_maxshield=True) 
