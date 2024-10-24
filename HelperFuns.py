# HelperFuns.py

import tkinter as tk
import time
from threading import Thread
from pynput import keyboard
import os
import random

def select_and_shuffle_channels(raw, bad_channels, channel_type, total_channels=15, max_bad_channels=3):
    """
    Selects and shuffles channels of a specific type, including a random selection of bad ones.

    Args:
        raw (mne.io.Raw): Raw data.
        bad_channels (list): List of known bad channels.
        channel_type (str): Type of channels to select ('EEG', 'Mag', 'Grad').
        total_channels (int): Total number of channels to select.
        max_bad_channels (int): Maximum number of bad channels to include.

    Returns:
        tuple: (selected_channels, bad_chans_in_display)
    """
    all_channels = raw.ch_names

    # Filter channels by type
    if channel_type == 'EEG':
        type_channels = [ch for ch in all_channels if ch.startswith('EEG')]
    elif channel_type == 'Mag':
        type_channels = [ch for ch in all_channels if ch.startswith('MEG') and ch.endswith('1')]
    elif channel_type == 'Grad':
        type_channels = [ch for ch in all_channels if ch.startswith('MEG') and ch.endswith(('2', '3'))]
    else:
        raise ValueError(f"Invalid channel type: {channel_type}")

    # Separate good and bad channels
    good_channels = [ch for ch in type_channels if ch not in bad_channels]
    bad_channels_in_type = [ch for ch in bad_channels if ch in type_channels]

    # Randomly select bad channels
    num_bad = min(random.randint(0, max_bad_channels), len(bad_channels_in_type))
    selected_bad_channels = random.sample(bad_channels_in_type, num_bad)

    # Randomly select good channels
    num_good = total_channels - num_bad
    selected_good_channels = random.sample(good_channels, min(num_good, len(good_channels)))

    # Combine and shuffle
    selected_channels = selected_good_channels + selected_bad_channels
    random.shuffle(selected_channels)

    return selected_channels, selected_bad_channels

def display_message(message, color='black', duration=1):
    """
    Displays a temporary message to the user.

    Args:
        message (str): Message to display.
        color (str): Text color.
        duration (int): Duration to display the message (in seconds).
    """
    root = tk.Tk()
    # Hide the root window drag bar and close button
    root.overrideredirect(True)
    # Make the root window always on top
    root.attributes('-topmost', True)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    # root.geometry(f"{screen_width}x{screen_height}+0+0")
    # label = tk.Label(root, text=message, fg=color, bg='white', font=('Helvetica', 48))
    label = tk.Label(root, text=message, fg=color, bg='black', font=('Helvetica', 72), padx=root.screen_width // 2,
                     pady=screen_height // 2)
    # label.pack(expand=True)
    label.pack()
    # Update the GUI
    # root.update()
    # Pause for 1 second
    # time.sleep(1)
    # Destroy the root
    # root.destroy()
    
    root.after(duration * 1000, root.destroy)
    root.mainloop()

def monitor_selections(fig, correct_selections, shared, feedback=True):
    """
    Monitors user selections (bad channels or components), provides feedback, and updates shared results.

    Args:
        fig: MNE figure object.
        correct_selections (list): List of correct bad channels or components.
        shared (dict): Shared dictionary to communicate between threads.
        feedback (bool): Whether to provide feedback to the user.
    """
    previous_selections = set()
    hits, false_alarms = 0, 0

    controller = keyboard.Controller()

    try:
        while not shared.get('done', False):
            current_selections = set(fig.mne.info['bads']) if hasattr(fig.mne, 'info') else set(fig.exclude)

            added = current_selections - previous_selections
            removed = previous_selections - current_selections

            # What is the space preesed thing????
            if shared.get('space_pressed', False):
                shared['space_pressed'] = False

            for item in added:
                if item in correct_selections:
                    hits += 1
                    if feedback:
                        display_message("Correct!", "green")
                else:
                    false_alarms += 1
                    if feedback:
                        display_message("Incorrect!", "red")

            previous_selections = current_selections

            if shared.get('tab_pressed', False):
                # Press tab to show that it's done
                shared['tab_pressed'] = False
                shared['done'] = True
                controller.press(keyboard.Key.esc)
                controller.release(keyboard.Key.esc)
                break

            time.sleep(1)
    except Exception as e:
        print(f"Error in monitor_selections: {e}")

    misses = len(set(correct_selections) - previous_selections)
    correct_rejections = len(correct_selections) - hits - misses

    shared.update({
        'hits': hits,
        'false_alarms': false_alarms,
        'misses': misses,
        'correct_rejections': correct_rejections
    })

def save_results(subj, ses, run, results, result_type, group_dir):
    """
    Saves the results to a CSV file.

    Args:
        participant_info (dict): Participant information (ID, session number, etc.).
        results (list): List of results dictionaries from trials.
        result_type (str): Type of result ('bads' or 'ICs').
        group_dir (str): Directory for the experimental group ('control' or 'experimental').
    """
    directory = os.path.join(group_dir, f"{result_type}_results")
    os.makedirs(directory, exist_ok=True)
    filename = f"results_{subj}_{ses}_{run}.csv"
    filepath = os.path.join(directory, filename)

    with open(filepath, 'w') as f:
        f.write('trial,hits,false_alarms,misses,correct_rejections\n')
        for i, trial_result in enumerate(results, 1):
            f.write(f"{i},{trial_result['hits']},{trial_result['false_alarms']},{trial_result['misses']},{trial_result['correct_rejections']}\n")

    print(f"Results saved to {filepath}")
