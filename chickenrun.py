import os
import numpy as np
import mne
import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
import pickle
import csv
import random
from slides import display_slides

def show_instructions():
    instructions1 = (
        "Welcome to this EEG and MEG data classification experiment! "
        "Some slides will be displayed on the screen to teach you how to recognize artifacts "
        "in EEG and MEG recordings. Take your time to read them; you can go back to review the slides. "
        "Once you are ready, you can close the slides window to start the experiment."
    )
    instructions2 = (
        "Then, EEG and MEG recordings will be displayed on the screen. "
        "You can scroll over time to examine the channels. If you think a channel is contaminated by artifacts, "
        "you can click on it."
    )
    instructions3 = (
        "You can select multiple channels or no channel at all. "
        "To validate your answer and display the next series of channels, you can press TAB. Good luck!"
    )
    messagebox.showinfo("Instructions - Page 1", instructions1)
    messagebox.showinfo("Instructions - Page 2", instructions2)
    messagebox.showinfo("Instructions - Page 3", instructions3)

def create_label_entry(window, text, row):
    label = tk.Label(window, text=text)
    label.grid(row=row, column=0)
    entry = tk.Entry(window)
    entry.grid(row=row, column=1)
    return entry

def run_experiment(participant_number, experience_level, session_number, feedback=True, group='experimental', n_trials=100):
    """
    Runs the EEG/MEG data classification experiment.

    Args:
        feedback (bool): Whether to provide feedback (True for experimental group, False for control group).
        group (str): Group name ('experimental' or 'control') used for saving results.
    """
    # Display slides (if any)
    slide_folder = 'slides'
    if os.path.exists(slide_folder):
        display_slides(slide_folder)

    data_path = 'data/trial_data'
    file_list = os.listdir(data_path)
    file_paths = np.random.choice(file_list, n_trials, replace=False)

    results = []
    for count, trial_file in enumerate(file_paths, start=1):
        # Load the trial data
        with open(os.path.join(data_path, trial_file), 'rb') as f:
            trial_data, bad_channels_in_display = pickle.load(f)
        print(f'Processing file: {trial_file} (Trial {count}/{n_trials})')
        n_channels = trial_data.info['nchan']

        # Shared data
        shared = {
            'hits': 0,
            'false_alarms': 0,
            'misses': 0,
            'correct_rejections': n_channels - len(bad_channels_in_display),
            'selected_channels': set(),
            'done': False,
            'previous_bads': set()
        }
        def display_feedback(fig, message, color='black'):
            # Remove previous feedback text
            if hasattr(display_feedback, 'text'):
                display_feedback.text.remove()
            # Add new feedback text
            display_feedback.text = fig.mne.ax_main.text(
                0.5, 1.01, message, transform=fig.mne.ax_main.transAxes,
                ha='center', va='bottom', color=color, fontsize=12
            )
            fig.canvas.draw_idle()

        def on_pick(event):
            artist = event.artist
            if isinstance(artist, plt.Text):
                ch_name = artist.get_text()
                ch_names = trial_data.info['ch_names']
                if ch_name in ch_names:
                    if ch_name in trial_data.info['bads']:
                        # Remove from bads
                        trial_data.info['bads'].remove(ch_name)
                        message = f"Unmarked {ch_name} as bad."
                        color = 'green' if ch_name not in bad_channels_in_display else 'red'
                    else:
                        # Add to bads
                        trial_data.info['bads'].append(ch_name)
                        message = f"Marked {ch_name} as bad."
                        color = 'green' if ch_name in bad_channels_in_display else 'red'
                    # Provide immediate feedback
                    display_feedback(fig, message, color)
                    
        def on_key(event):
            if event.key == 'tab':
                # Finish the trial
                fig.canvas.mpl_disconnect(cid_pick)
                fig.canvas.mpl_disconnect(cid_key)
                plt.close(fig)

                # Evaluate results
                selected = shared['selected_channels']
                hits = len(selected & set(bad_channels_in_display))
                false_alarms = len(selected - set(bad_channels_in_display))
                misses = len(set(bad_channels_in_display) - selected)
                correct_rejections = n_channels - len(selected | set(bad_channels_in_display))
                shared['hits'] = hits
                shared['false_alarms'] = false_alarms
                shared['misses'] = misses
                shared['correct_rejections'] = correct_rejections
                # Add feedback if needed
                if feedback:
                    messagebox.showinfo(
                        "Feedback",
                        f"Hits: {hits}\nFalse Alarms: {false_alarms}\nMisses: {misses}\nCorrect Rejections: {correct_rejections}"
                    )

                # Proceed to next trial
                plt.close('all')

        # Open interactive window
        fig = trial_data.plot(
            n_channels=n_channels,
            duration=2,
            block=False,
            show=False,
            picks='all',
            title=f'Trial {count}/{n_trials}',
            proj=False,
            show_scrollbars=True
        )

        # Connect event handlers
        cid_pick = fig.canvas.mpl_connect('pick_event', on_pick)
        cid_key = fig.canvas.mpl_connect('key_press_event', on_key)

        # Show the plot and start the event loop
        plt.show(block=True)

        # Collect results
        trial_results = {
            'hits': shared.get('hits', 0),
            'false_alarms': shared.get('false_alarms', 0),
            'misses': shared.get('misses', 0),
            'correct_rejections': shared.get('correct_rejections', 0)
        }
        results.append(trial_results)

    # Save results to a CSV file
    output_filename = f"results_{participant_number}_{session_number}_{group}.csv"
    with open(output_filename, 'w', newline='') as csvfile:
        fieldnames = ['Trial', 'Hits', 'False Alarms', 'Misses', 'Correct Rejections']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for i, trial_result in enumerate(results, start=1):
            writer.writerow({
                'Trial': i,
                'Hits': trial_result['hits'],
                'False Alarms': trial_result['false_alarms'],
                'Misses': trial_result['misses'],
                'Correct Rejections': trial_result['correct_rejections']
            })
    print('Experiment completed. Results saved.')

def on_submit():
    # Retrieve participant information
    participant_number = participant_number_entry.get()
    experience_level = experience_level_entry.get()
    session_number = session_number_entry.get()

    # Validate experience level
    if not experience_level.isdigit() or not (1 <= int(experience_level) <= 4):
        messagebox.showerror("Invalid Input", "Experience level must be a number between 1 and 4.")
        return
    window.destroy()
    show_instructions()

    run_experiment(participant_number, experience_level, session_number, feedback=feedback, group=group)

if __name__ == "__main__":
    # Ask the user to select the group type
    root = tk.Tk()
    root.withdraw()
    group_choice = messagebox.askquestion(
        "Group Selection",
        "Is this the experimental group? Click 'Yes' for Experimental, 'No' for Control."
    )
    if group_choice == 'yes':
        feedback = True
        group = 'experimental'
    else:
        feedback = False
        group = 'control'
    window = tk.Tk()
    window.title("Participant Information")
    participant_number_entry = create_label_entry(window, "Participant Number:", 0)
    experience_level_entry = create_label_entry(window, "Experience Level (1-4, from very experienced to fully naïve):", 1)
    session_number_entry = create_label_entry(window, "Session Number:", 2)
    submit_button = tk.Button(window, text="Submit", command=on_submit)
    submit_button.grid(row=3, column=0, columnspan=2)
    window.mainloop()
