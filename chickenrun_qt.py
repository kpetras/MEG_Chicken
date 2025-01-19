import os
import numpy as np
import mne
import tkinter as tk
from tkinter import messagebox
import pickle
import csv
import sys
from slides import display_slides
from ica_plot import custome_ica_plot
from HelperFuns import create_label_entry
import json
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
import contextlib
import io

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

def run_experiment(participant_number, experience_level, session_number, feedback=True, n_trials=10, mode_ica=True, deselect = False, ch_type = 'eeg'):
    """
    Runs the EEG/MEG data classification experiment.

    Args:
        feedback (bool): Whether to provide feedback (True for experimental group, False for control group).
        n_trials (ind): Total number of trials.
        mode_ica (bool): Whether to include ICA functionality.
    """

    if not mode_ica:
        data_path = os.path.join('data', 'trial_data')
        file_list =  [f for f in os.listdir(data_path) if not f.startswith('.')]
        file_paths = np.random.choice(file_list, n_trials, replace=False)

        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        # Create a separate window to display print outputs
        class OutputWindow(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("Trial Feedback")
                self.setGeometry(700, 100, 400, 300)
                
                # Set up text area
                self.text_area = QTextEdit(self)
                self.text_area.setReadOnly(True)
                
                # Layout
                layout = QVBoxLayout()
                layout.addWidget(self.text_area)
                container = QWidget()
                container.setLayout(layout)
                self.setCentralWidget(container)
                
            def write(self, message):
                # Clear previous text and display only the latest message
                self.text_area.clear()
                self.text_area.setPlainText(message.strip()) 

            def flush(self):
                pass  # Necessary for compatibility with sys.stdout redirection


        # Create the output window
        output_window = OutputWindow()
        output_window.show()

        # Redirect print statements to the output window
        class PrintRedirector:
            def __init__(self, output_widget):
                self.output_widget = output_widget
            
            def write(self, message):
                # Display only the latest print message
                if message.strip():  # Avoids displaying empty messages
                    self.output_widget.write(message)
            
            def flush(self):
                self.output_widget.flush()

        # Redirect sys.stdout to the output window
        sys.stdout = PrintRedirector(output_window)
    else:
        data_path = os.path.join('data', 'ica')
        file_paths = [f for f in os.listdir(data_path) if f.endswith('_ica.fif')]

    results = []
    for count, trial_file in enumerate(file_paths, start=1):
        # Load the trial data for non-ica
        if not mode_ica:
            with open(os.path.join(data_path, trial_file), 'rb') as f:
                trial_data, bad_channels_in_display = pickle.load(f)
            # print(f'Processing file: {trial_file} (Trial {count}/{n_trials})')
            n_channels = trial_data.info['nchan']
        else:
            # load ica information
            mne.viz.set_browser_backend('matplotlib')
            with open('config.json', 'r') as file:
                config_data = json.load(file)
            subj, ses, run = trial_file.split('_')[:3]
            run_ind = run + '.fif'
            ICA_remove_inds = config_data.get("ICA_remove_inds", {})
            ICA_remove_inds_list = ICA_remove_inds[subj][run_ind][ch_type]

        if not mode_ica:
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
            # Use contextlib to avoid unnecessary message when open the mne browser
            with contextlib.redirect_stdout(io.StringIO()):
                fig = trial_data.plot(
                    n_channels=n_channels,
                    duration=2,
                    block=False
                )

            # Define the function to check for changes
            def check_bads():
                curr_bads = set(str(ch) for ch in fig.mne.info['bads'])
                new_bad = curr_bads.symmetric_difference(shared['selected_channels'])
                if new_bad:
                    new_bad = new_bad.pop()
                    if new_bad in shared['selected_channels']:
                        if deselect:
                            shared['selected_channels'].remove(new_bad)
                            correct = 'Correct' if new_bad not in bad_channels_in_display else 'Wrong'
                            print(f"{correct}! Unmarked {new_bad} as bad.")
                        else:
                            print("Deselection OFF: Only the first try is registered.")
                    else:
                            shared['selected_channels'].add(new_bad)
                            correct = 'Correct' if new_bad in bad_channels_in_display else 'Wrong'
                            print(f"{correct}! Marked {new_bad} as bad.") 

            # Create a QTimer to check periodically
            timer = QTimer()
            timer.timeout.connect(check_bads)
            timer.start(500)  # Check every 500 milliseconds

            # Define a function to handle browser close event
            def on_browser_close(event):
                timer.stop()  # Stop the timer

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
                print(f"hits: {shared['hits']} \n"
                    f"false alarms: {shared['false_alarms']} \n"
                    f"misses = {shared['misses']} \n"
                    f"correct rejections = {shared['correct_rejections']} \n")
                # Collect results
                trial_results = {
                    'hits': shared.get('hits', 0),
                    'false_alarms': shared.get('false_alarms', 0),
                    'misses': shared.get('misses', 0),
                    'correct_rejections': shared.get('correct_rejections', 0)
                }
                results.append(trial_results)
                app.quit()    # Quit the application
                event.accept()  # Accept the close event

            # Override the browser's closeEvent to call on_browser_close
            fig.closeEvent = on_browser_close

            # Show the browser
            fig.show()

            # Start the Qt event loop
            app.exec_()
#######################################################
        else: 
            file_path = os.path.join('data', 'ica' ,trial_file)
            ica = mne.preprocessing.read_ica(file_path)
            raw_file_name = subj + '_'+ ses +'_'+ run + '_preprocessed_raw.fif'
            raw_file_path = os.path.join('data', 'preprocessed',raw_file_name)
            raw_preprocessed = mne.io.read_raw_fif(raw_file_path, preload=True, allow_maxshield=True)
            
            shared = {
                'hits': 0,
                'false_alarms': 0,
                'misses': 0,
                'correct_rejections': 0,
                'done': False,
                'previous_exclude': set(ica.exclude)
            }        

            # Show the plot and start the event loop
            n_components = 50 # number of components per page
            fig = custome_ica_plot(ica, ICA_remove_inds_list, feedback, deselect, nrows = 5, ncols = 10, inst = raw_preprocessed)
            def on_close(event):
                print('on close')
                fig.canvas.mpl_disconnect(cid_key)
                # Evaluate results
                selected = set(ica.exclude)
                hits = len(selected & set(ICA_remove_inds_list))
                false_alarms = len(selected - set(ICA_remove_inds_list))
                misses = len(set(ICA_remove_inds_list) - selected)
                correct_rejections = n_components - len(selected | set(ICA_remove_inds_list))
                shared['hits'] = hits
                shared['false_alarms'] = false_alarms
                shared['misses'] = misses
                shared['correct_rejections'] = correct_rejections
                if feedback:
                    messagebox.showinfo(
                        "Feedback",
                        f"Hits: {hits}\nFalse Alarms: {false_alarms}\nMisses: {misses}\nCorrect Rejections: {correct_rejections}"
                    )

                # Proceed to next trial
                plt.close(fig)
                plt.close('all')
            cid_key = fig.canvas.mpl_connect('close_event', on_close)
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
    output_filename = f"results_{participant_number}_{session_number}_{experience_level}_{'exp' if feedback else 'ctrl'}.csv"
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
    plt.close('all')  # Ensure all matplotlib windows are closed.
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
        # Display slides (if any)
        slide_folder = 'slides'
        if os.path.exists(slide_folder):
            display_slides(slide_folder, master=window)
    window.destroy()

    run_experiment(participant_number, experience_level, session_number, feedback=feedback, deselect = deselect, mode_ica = mode_ica)


if __name__ == "__main__":
    window = tk.Tk()
    window.title("Participant Information")
    participant_number_entry = create_label_entry(window, "Participant Number:", 0)
    experience_level_entry = create_label_entry(window, "Experience Level \n (1-4, from very experienced to fully naïve):", 1)
    session_number_entry = create_label_entry(window, "Session Number:", 2)

        # Checkbox to enable or disable feedback
    feedback_var = tk.BooleanVar(value=False) # Unchecked by default
    feedback_checkbox = tk.Checkbutton(window, text="Enable Immediate Feedback", variable=feedback_var)
    feedback_checkbox.grid(row=3, column=1, columnspan=2, sticky="w")

    show_instruc_var = tk.BooleanVar(value=False) # Unchecked by default
    instruc_checkbox = tk.Checkbutton(window, text="Show Instruction", variable=show_instruc_var)
    instruc_checkbox.grid(row=4, column=1, columnspan=2, sticky="w")

    deselect_var = tk.BooleanVar(value = False) # Unchecked by default
    deselect_checkbox = tk.Checkbutton(window, text="Enable Deselect", variable=deselect_var)
    deselect_checkbox.grid(row=5, column=1, columnspan=2, sticky="w")

    mode_var = tk.StringVar(value="ICA")  # Default selection is "ICA"
    radio_ica = tk.Radiobutton(window, text="ICA", variable=mode_var, value="ICA")
    radio_ica.grid(row=3, column=0, sticky="w")
    radio_eeg_meg = tk.Radiobutton(window, text="EEG/MEG", variable=mode_var, value="EEG/MEG")
    radio_eeg_meg.grid(row=4, column=0, sticky="w")

    submit_button = tk.Button(window, text="Submit", command=on_submit)
    submit_button.grid(row=6, column=0, columnspan=2)
    window.mainloop()
