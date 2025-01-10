import os
import numpy as np
import mne
import tkinter as tk
from tkinter import messagebox
import pickle
import csv
import random
from slides import display_slides
from ica_plot import custome_ica_plot
import json
import matplotlib
mne.viz.set_browser_backend('matplotlib')
matplotlib.use('tkagg')
import matplotlib.pyplot as plt

def show_instructions():
    instructions1 = (
        "Welcome to this EEG and MEG data classification experiment! "
        "Some slides will be displayed on the screen to teach you how to recognize artifacts "
        "in EEG and MEG recordings. Take your time to read them..."
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

def run_experiment(participant_number, 
                   experience_level, 
                   session_number, 
                   feedback=True, 
                   n_trials=10, 
                   mode_ica=True, 
                   deselect=False,
                   channel_types=None):
    """
    Runs the EEG/MEG (or ICA) data classification experiment.

    Args:
        participant_number (str): ...
        experience_level (str): ...
        session_number (str): ...
        feedback (bool): Whether to provide feedback.
        n_trials (int): Total number of trials (for non-ICA or for ICA).
        mode_ica (bool): Whether to use ICA data or raw trials.
        deselect (bool): Whether to allow deselection of channels.
        channel_types (list[str] or None): e.g. ["EEG", "Mag", "Grad"].
    """

    if channel_types is None:
        channel_types = ["eeg", "mag", "grad"]

    results = []

    if not mode_ica:
        data_path = os.path.join('data', 'trial_data')
        
        all_files = []
        for ch_type in channel_types:
            ch_dir = os.path.join(data_path, ch_type)
            if os.path.isdir(ch_dir):
                files_in_ch_dir = [
                    f for f in os.listdir(ch_dir) 
                    if f.startswith('trial_') and f.endswith('.pkl')
                ]
                files_in_ch_dir = [os.path.join(ch_dir, f) for f in files_in_ch_dir]
                all_files.extend(files_in_ch_dir)
            else:
                print(f"Warning: {ch_dir} not found or is not a directory.")
        
        if len(all_files) == 0:
            print("No trial files found for the specified channel_types.")
            return
        
        file_paths = np.random.choice(all_files, min(n_trials, len(all_files)), replace=False)

        for count, trial_file in enumerate(file_paths, start=1):
            with open(trial_file, 'rb') as f:
                trial_dict = pickle.load(f)
            trial_data = trial_dict["data"]
            bad_channels_in_display = trial_dict["bad_chans_in_display"]
            channel_type = trial_dict.get("channel_type", "Unknown")

            print(f'Processing file: {os.path.basename(trial_file)} (Trial {count}/{n_trials})')
            print(f"Channel type: {channel_type}")
            n_channels = trial_data.info['nchan']

            shared = {
                'hits': 0,
                'false_alarms': 0,
                'misses': 0,
                'correct_rejections': n_channels - len(bad_channels_in_display),
                'selected_channels': set(),
                'done': False
            }

            def on_pick(event):
                artist = event.artist
                if isinstance(artist, plt.Text):
                    ch_name = artist.get_text()
                    ch_names = trial_data.info['ch_names']
                    if ch_name in ch_names:
                        if ch_name in shared['selected_channels']:
                            if deselect:
                                shared['selected_channels'].remove(ch_name)
                                message = f"Unmarked {ch_name} as bad."
                                color = ('green' if ch_name not in bad_channels_in_display else 'red')
                            else:
                                message = "Deselection OFF: Only the first try is registered."
                                color = 'red'
                        else:
                            shared['selected_channels'].add(ch_name)
                            message = f"Marked {ch_name} as bad."
                            color = ('green' if ch_name in bad_channels_in_display else 'red')
                        
                        if feedback:
                            display_feedback(fig, message, color)
                        
            def on_key(event):
                if event.key == 'tab':
                    # Finish the trial
                    fig.canvas.mpl_disconnect(cid_pick)
                    fig.canvas.mpl_disconnect(cid_key)
                    plt.close(fig)

                    selected = shared['selected_channels']
                    hits = len(selected & set(bad_channels_in_display))
                    false_alarms = len(selected - set(bad_channels_in_display))
                    misses = len(set(bad_channels_in_display) - selected)
                    correct_rejections = n_channels - len(selected | set(bad_channels_in_display))
                    shared['hits'] = hits
                    shared['false_alarms'] = false_alarms
                    shared['misses'] = misses
                    shared['correct_rejections'] = correct_rejections

                    if feedback:
                        messagebox.showinfo(
                            "Feedback",
                            f"Channel type: {channel_type}\n\n"
                            f"Hits: {hits}\n"
                            f"False Alarms: {false_alarms}\n"
                            f"Misses: {misses}\n"
                            f"Correct Rejections: {correct_rejections}"
                        )

                    plt.close('all')

            fig = trial_data.plot(
                n_channels=n_channels,
                duration=2,
                block=False,
                title=f"Trial {count}/{n_trials} - {channel_type}"
            )
            cid_pick = fig.canvas.mpl_connect('pick_event', on_pick)
            cid_key = fig.canvas.mpl_connect('key_press_event', on_key)
            plt.show(block=True)

            trial_results = {
                'channel_type': channel_type,
                'hits': shared.get('hits', 0),
                'false_alarms': shared.get('false_alarms', 0),
                'misses': shared.get('misses', 0),
                'correct_rejections': shared.get('correct_rejections', 0)
            }
            results.append(trial_results)
    
    else:
        data_path = os.path.join('data', 'ica')

        all_ica_files = []
        for ch_type in channel_types:
            ch_dir = os.path.join(data_path, ch_type)
            if not os.path.isdir(ch_dir):
                print(f"Warning: {ch_dir} not found or not a directory.")
                continue
            
            files_in_ch_dir = [f for f in os.listdir(ch_dir) if f.endswith('_ica.fif')]
            for ica_file in files_in_ch_dir:
                full_path = os.path.join(ch_dir, ica_file)
                all_ica_files.append((ch_type, full_path))
        
        if len(all_ica_files) == 0:
            print("No ICA files found for the specified channel_types.")
            return

        selected_ica = random.sample(all_ica_files, min(n_trials, len(all_ica_files)))

        with open('config.json', 'r') as file:
            config_data = json.load(file)
        ica_remove = config_data.get("ICA_remove_inds", {})

        for count, (ch_type, ica_path) in enumerate(selected_ica, start=1):
            ica_filename = os.path.basename(ica_path)
            print(f"Processing ICA file: {ica_filename} (Trial {count}/{n_trials}), channel_type={ch_type}")

            subj, ses, run = ica_filename.split('_')[:3]
            run_ind = run + '.fif'

            ica = mne.preprocessing.read_ica(ica_path)

            raw_file_name = subj + '_' + ses + '_' + run + '_preprocessed_raw.fif'
            raw_file_path = os.path.join('data', 'preprocessed', raw_file_name)
            raw_preprocessed = mne.io.read_raw_fif(raw_file_path, preload=True, allow_maxshield=True)
            

            ica_remove_inds_list = ica_remove[subj][run_ind][ch_type]

            shared = {
                'hits': 0,
                'false_alarms': 0,
                'misses': 0,
                'correct_rejections': 0,
                'previous_exclude': set(ica.exclude)
            }

            n_components = len(ica.get_components())
            fig = custome_ica_plot(
                ica,
                ica_remove_inds_list,
                feedback,
                deselect,
                nrows=5,
                ncols=10,
                inst=raw_preprocessed
            )

            def on_close(event):
                # Finish the trial
                fig.canvas.mpl_disconnect(cid_close)
                plt.close(fig)

                selected = set(ica.exclude)
                hits = len(selected & set(ica_remove_inds_list))
                false_alarms = len(selected - set(ica_remove_inds_list))
                misses = len(set(ica_remove_inds_list) - selected)
                correct_rejections = n_components - len(selected | set(ica_remove_inds_list))

                shared['hits'] = hits
                shared['false_alarms'] = false_alarms
                shared['misses'] = misses
                shared['correct_rejections'] = correct_rejections

                if feedback:
                    messagebox.showinfo(
                        "Feedback",
                        f"channel_type: {ch_type}\n\n"
                        f"Hits: {hits}\n"
                        f"False Alarms: {false_alarms}\n"
                        f"Misses: {misses}\n"
                        f"Correct Rejections: {correct_rejections}"
                    )

                plt.close('all')

            cid_close = fig.canvas.mpl_connect('close_event', on_close)
            plt.show(block=True)

            trial_results = {
                'channel_type': ch_type,
                'hits': shared.get('hits', 0),
                'false_alarms': shared.get('false_alarms', 0),
                'misses': shared.get('misses', 0),
                'correct_rejections': shared.get('correct_rejections', 0)
            }
            results.append(trial_results)

    output_filename = f"results_{participant_number}_{session_number}_{experience_level}_{'exp' if feedback else 'ctrl'}.csv"
    with open(output_filename, 'w', newline='') as csvfile:
        fieldnames = ['Trial', 'channel_type', 'Hits', 'False Alarms', 'Misses', 'Correct Rejections']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for i, trial_result in enumerate(results, start=1):
            writer.writerow({
                'Trial': i,
                'channel_type': trial_result.get('channel_type', 'Unknown'),
                'Hits': trial_result['hits'],
                'False Alarms': trial_result['false_alarms'],
                'Misses': trial_result['misses'],
                'Correct Rejections': trial_result['correct_rejections']
            })

    plt.close('all')
    print('Experiment completed. Results saved.')

def on_submit():
    participant_number = participant_number_entry.get()
    experience_level = experience_level_entry.get()
    session_number = session_number_entry.get()
    feedback = feedback_var.get()
    show_instruc = show_instruc_var.get()
    deselect = deselect_var.get()
    mode_ica = (mode_var.get() == "ICA")

    print("Feedback Enabled:", feedback)
    print("Show Instructions:", show_instruc)
    print("Deselect Enabled:", deselect)
    print("Mode ICA:", mode_ica)

    if not participant_number.isdigit():
        messagebox.showerror("Invalid Input", "Participant number must be a number.")
        return
    if not session_number.isdigit():
        messagebox.showerror("Invalid Input", "Session number must be a number.")
        return
    if not experience_level.isdigit() or not (1 <= int(experience_level) <= 4):
        messagebox.showerror("Invalid Input", "Experience level must be a number between 1 and 4.")
        return
    
    if show_instruc: 
        show_instructions()
        slide_folder = 'slides'
        if os.path.exists(slide_folder):
            display_slides(slide_folder, master=window)
    window.destroy()

    selected_channel_types = []
    if eeg_var.get():
        selected_channel_types.append("eeg")
    if mag_var.get():
        selected_channel_types.append("mag")
    if grad_var.get():
        selected_channel_types.append("grad")
    # Assume all if none chosen
    if not selected_channel_types:
        selected_channel_types = ["eeg", "mag", "grad"]

    run_experiment(
        participant_number, 
        experience_level, 
        session_number, 
        feedback=feedback, 
        deselect=deselect, 
        mode_ica=mode_ica,
        channel_types=selected_channel_types
    )

if __name__ == "__main__":
    window = tk.Tk()
    window.title("Participant Information")
    
    participant_number_entry = create_label_entry(window, "Participant Number:", 0)
    experience_level_entry = create_label_entry(window, "Experience Level \n (1-4, from very experienced to fully naïve):", 1)
    session_number_entry = create_label_entry(window, "Session Number:", 2)

    feedback_var = tk.BooleanVar(value=False)
    feedback_checkbox = tk.Checkbutton(window, text="Enable Immediate Feedback", variable=feedback_var)
    feedback_checkbox.grid(row=3, column=1, columnspan=2, sticky="w")

    show_instruc_var = tk.BooleanVar(value=False)
    instruc_checkbox = tk.Checkbutton(window, text="Show Instruction", variable=show_instruc_var)
    instruc_checkbox.grid(row=4, column=1, columnspan=2, sticky="w")

    deselect_var = tk.BooleanVar(value=False)
    deselect_checkbox = tk.Checkbutton(window, text="Enable Deselect", variable=deselect_var)
    deselect_checkbox.grid(row=5, column=1, columnspan=2, sticky="w")

    mode_var = tk.StringVar(value="ICA")
    radio_ica = tk.Radiobutton(window, text="ICA", variable=mode_var, value="ICA")
    radio_ica.grid(row=3, column=0, sticky="w")
    radio_eeg_meg = tk.Radiobutton(window, text="EEG/MEG", variable=mode_var, value="EEG/MEG")
    radio_eeg_meg.grid(row=4, column=0, sticky="w")

    eeg_var = tk.BooleanVar(value=True)
    cb_eeg = tk.Checkbutton(window, text="EEG", variable=eeg_var)
    cb_eeg.grid(row=6, column=0, sticky="w")

    mag_var = tk.BooleanVar(value=True)
    cb_mag = tk.Checkbutton(window, text="Mag", variable=mag_var)
    cb_mag.grid(row=6, column=1, sticky="w")

    grad_var = tk.BooleanVar(value=True)
    cb_grad = tk.Checkbutton(window, text="Grad", variable=grad_var)
    cb_grad.grid(row=6, column=2, sticky="w")

    submit_button = tk.Button(window, text="Submit", command=on_submit)
    submit_button.grid(row=7, column=0, columnspan=3)

    window.mainloop()
