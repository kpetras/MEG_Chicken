import os
import time
import random
import json
import numpy as np
import mne
import tkinter as tk
from tkinter import messagebox
import pickle
import csv
import matplotlib
import matplotlib.pyplot as plt
import warnings
from ica_plot import custome_ica_plot
from FeedbackWindow import FeedbackWindow, TrialResultWindow
from scipy.stats import norm
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
# ============ MNE Matplotlib settings ============
mne.viz.set_browser_backend('matplotlib')
matplotlib.use('tkagg')

warnings.filterwarnings(
    'ignore',
    message='Projection vector.*has been reduced to',
    category=RuntimeWarning
)

try:
    from slides import display_slides
except ImportError:
    def display_slides(*args, **kwargs):
        pass


def compute_dprime(hits, false_alarms, misses, correct_rejections):
    """
    Compute d-prime based on hits/misses/false alarms/correct rejections.
    
    D-prime = Z(HR) - Z(FAR)
    Where:
    HR = hits / (hits + misses)
    FAR = false_alarms / (false_alarms + correct_rejections)
    """
    total_signal = hits + misses
    total_noise  = false_alarms + correct_rejections

    if total_signal == 0 or total_noise == 0:
        return 0.0

    pHit = (hits + 0.5) / (total_signal + 1.0)
    pFA  = (false_alarms + 0.5) / (total_noise + 1.0)    

    # Convert to Z scores, no error checking
    zHit = norm.ppf(pHit)
    zFA = norm.ppf(pFA)

    dprime = zHit - zFA

    # crit = (zHit + zFA) / -2
    # crit_prime = crit / dprime    
    return dprime


class MEG_Chicken:
    def __init__(self):
        """ The main window for collecting participant info. """
        self.window = tk.Tk()
        self.window.title("Participant Information")

        self.open_windows = [] # To register the opened windows so that we can actually close them all...
        self.results = []  # store trial-wise dict
        self.trial_accuracies = []

        # for overall timing
        self.global_start_time = None 

        # UI for participant settings
        self.participant_number_entry = self.create_label_entry(self.window, "Participant Number:", 0)
        # What's the point but... yeah... I'm keeping this tho
        self.experience_level_entry = self.create_label_entry(self.window, "Experience Level (1-4):", 1)
        self.session_number_entry = self.create_label_entry(self.window, "Session Number:", 2)

        self.feedback_var = tk.BooleanVar(value=False)
        feedback_checkbox = tk.Checkbutton(self.window, text="Enable Immediate Feedback", variable=self.feedback_var)
        feedback_checkbox.grid(row=3, column=1, columnspan=2, sticky="w")

        self.show_instruc_var = tk.BooleanVar(value=False)
        instruc_checkbox = tk.Checkbutton(self.window, text="Show Instruction", variable=self.show_instruc_var)
        instruc_checkbox.grid(row=4, column=1, columnspan=2, sticky="w")

        self.deselect_var = tk.BooleanVar(value=False)
        deselect_checkbox = tk.Checkbutton(self.window, text="Enable Deselect", variable=self.deselect_var)
        deselect_checkbox.grid(row=5, column=1, columnspan=2, sticky="w")

        self.mode_var = tk.StringVar(value="ICA")
        radio_ica = tk.Radiobutton(self.window, text="ICA", variable=self.mode_var, value="ICA")
        radio_ica.grid(row=3, column=0, sticky="w")
        radio_eeg_meg = tk.Radiobutton(self.window, text="EEG/MEG", variable=self.mode_var, value="EEG/MEG")
        radio_eeg_meg.grid(row=4, column=0, sticky="w")

        self.eeg_var = tk.BooleanVar(value=True)
        cb_eeg = tk.Checkbutton(self.window, text="EEG", variable=self.eeg_var)
        cb_eeg.grid(row=6, column=0, sticky="w")

        self.mag_var = tk.BooleanVar(value=True)
        cb_mag = tk.Checkbutton(self.window, text="Mag", variable=self.mag_var)
        cb_mag.grid(row=6, column=1, sticky="w")

        self.grad_var = tk.BooleanVar(value=True)
        cb_grad = tk.Checkbutton(self.window, text="Grad", variable=self.grad_var)
        cb_grad.grid(row=6, column=2, sticky="w")

        submit_button = tk.Button(self.window, text="Submit", command=self.on_submit)
        submit_button.grid(row=7, column=0, columnspan=3)

    def create_label_entry(self, window, text, row):
        label = tk.Label(window, text=text)
        label.grid(row=row, column=0)
        entry = tk.Entry(window)
        entry.grid(row=row, column=1)
        return entry

    def on_submit(self):
        """ Validate input, optionally show instructions, then run the experiment. """
        participant_number = self.participant_number_entry.get()
        experience_level = self.experience_level_entry.get()
        session_number = self.session_number_entry.get()
        feedback = self.feedback_var.get()
        show_instruc = self.show_instruc_var.get()
        deselect = self.deselect_var.get()
        mode_ica = (self.mode_var.get() == "ICA")

        if not participant_number.isdigit():
            messagebox.showerror("Invalid Input", "Participant number must be a number.")
            return
        if not session_number.isdigit():
            messagebox.showerror("Invalid Input", "Session number must be a number.")
            return
        if not experience_level.isdigit() or not (1 <= int(experience_level) <= 4):
            messagebox.showerror("Invalid Input", "Experience level must be 1 ~ 4.")
            return

        # Show instructions if needed
        if show_instruc:
            self.show_instructions()

        # Collect chosen channel types
        selected_channel_types = []
        if self.eeg_var.get():
            selected_channel_types.append("eeg")
        if self.mag_var.get():
            selected_channel_types.append("mag")
        if self.grad_var.get():
            selected_channel_types.append("grad")
        if not selected_channel_types:
            selected_channel_types = ["eeg", "mag", "grad"]

        # Hide the participant info window
        self.window.withdraw()

        # Run
        self.run_experiment(
            participant_number,
            experience_level,
            session_number,
            feedback=feedback,
            mode_ica=mode_ica,
            deselect=deselect,
            channel_types=selected_channel_types
        )

    def show_instructions(self):
        instructions1 = (
            "Welcome to this EEG/MEG data classification experiment!\n"
            "Some slides might be displayed here to teach you how to recognize artifacts."
        )
        instructions2 = (
            "Then, raw EEG/MEG signals or ICA components will be displayed.\n"
            "If you think they are contaminated by artifacts, you can click on them."
        )
        instructions3 = (
            "You can select multiple channels/ICA-components or none.\n"
            "Press TAB to validate your answer and proceed to the next trial. Good luck!"
        )
        messagebox.showinfo("Instructions - Page 1", instructions1)
        messagebox.showinfo("Instructions - Page 2", instructions2)
        messagebox.showinfo("Instructions - Page 3", instructions3)

        slide_folder = 'slides'
        if os.path.exists(slide_folder):
            display_slides(slide_folder, master=self.window)

    def run_experiment(self,
                       participant_number,
                       experience_level,
                       session_number,
                       feedback=True,
                       n_trials=50,
                       mode_ica=True,
                       deselect=False,
                       channel_types=None):
        """
        Output: 
        1. trial results in CSV.
        2. Experiment response time in CSV
        """
        # Initialize the always-open trial result window to show default instruction
        self.trial_result_window = TrialResultWindow(master=self.window)
        self.open_windows.append(self.trial_result_window.master)

        # The experiment "global" start time
        self.global_start_time = time.time()

        if channel_types is None:
            channel_types = ["eeg", "mag", "grad"]

        if mode_ica:
            # =======================================================
            #                    ICA mode 
            # =======================================================
            # Go find files (from ICA folders since trial files are just for EEG)
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

            # Randomly selecting files according to the params
            chosen_ica_files = random.sample(all_ica_files, min(n_trials, len(all_ica_files)))

            # Yes, I know it's loading the whole file
            ica_remove = {}
            config_file = 'config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r') as file:
                    config_data = json.load(file)
                ica_remove = config_data.get("ICA_remove_inds", {})


            
            for trial_idx, (ch_type, ica_path) in enumerate(chosen_ica_files, start=1):
                ica_filename = os.path.basename(ica_path)
                print(f"[ICA Mode] Processing: {ica_filename} (Trial {trial_idx}/{n_trials}), channel_type={ch_type}")

                name_split = ica_filename.split('_')
                try:
                    subj, ses, run = name_split[0], name_split[1], name_split[2]
                except IndexError:
                    subj, ses, run = "unknown_subj", "unknown_ses", "unknown_run"

                ica = mne.preprocessing.read_ica(ica_path)
                raw_dir = os.path.join('data', 'preprocessed')
                raw_file_name = subj + '_' + ses + '_' + run + '_preprocessed_raw.fif'
                raw_file_path = os.path.join(raw_dir, raw_file_name)
                if not os.path.exists(raw_file_path):
                    print(f"Cannot find {raw_file_path}. Skipping trial.")
                    continue
                raw_preprocessed = mne.io.read_raw_fif(raw_file_path, preload=True, allow_maxshield=True)

                # Answers
                run_ind = run + '.fif'
                bad_components = []
                if (subj in ica_remove) and (run_ind in ica_remove[subj]) and (ch_type in ica_remove[subj][run_ind]):
                    bad_components = ica_remove[subj][run_ind][ch_type]

                print(bad_components)
                selected_components = set()

                fig = custome_ica_plot(
                    ica,
                    ICA_remove_inds_list=bad_components,
                    feedback=feedback,
                    deselect=deselect,
                    inst=raw_preprocessed,
                    nrows=5,
                    ncols=10,
                    master = self.window
                )
                # Trial start time after plotting since it takes some time to initialize
                # Not exactly sure to use real time or interval
                #trial_start_time = time.time() - self.global_start_time
                trial_start_time = time.time()

                selected_comps = set()                         

                def on_close_ica_fig(event):
                    """When the ICA figure is closed, finalize the trial metrics."""
                    # Register the time when click close
                    trial_end_time = time.time()
                    
                    fig.canvas.mpl_disconnect(cid_close)
                    plt.close(fig)

                    selected_comps.update(ica.exclude)

                    # compute hits / false alarms, etc.
                    hits = len(set(bad_components) & selected_comps)
                    false_alarms = len(selected_comps - set(bad_components))
                    misses = len(set(bad_components) - selected_comps)
                    n_components = len(ica.get_components())
                    correct_rejections = n_components - len(set(bad_components) | selected_comps)

                    denom = hits + false_alarms + misses + correct_rejections
                    accuracy = (hits + correct_rejections) / denom if denom > 0 else 0
                    dprime_val = compute_dprime(hits, false_alarms, misses, correct_rejections)

                    # if feedback: # Or no feedback at all when no feedback?
                    messagebox.showinfo(
                        "Trial Feedback",
                        f"Trial {trial_idx} ended!\n\n"
                        f"Hits: {hits}\nFalse Alarms: {false_alarms}\n"
                        f"Misses: {misses}\nCorrect Rejections: {correct_rejections}\n"
                        f"Accuracy: {accuracy*100:.1f}%\nD-prime: {dprime_val:.3f}"
                    )

                    # Update the always-open line chart with the new accuracy
                    # self.trial_result_window.update_accuracy(accuracy)
                    self._update_accuracy_safely(trial_idx, accuracy)
                    # Store the result
                    row_dict = {
                        'Trial': trial_idx,
                        'StartTime_s': trial_start_time,
                        'EndTime_s': trial_end_time,
                        'ChannelType': ch_type,
                        'SelectedChannels': ",".join(str(x) for x in sorted(selected_comps)),
                        'BadChannels': ",".join(str(x) for x in sorted(bad_components)),
                        'Hits': hits,
                        'FalseAlarms': false_alarms,
                        'Misses': misses,
                        'CorrectRejections': correct_rejections,
                        'Accuracy': accuracy,
                        'Dprime': dprime_val
                    }
                    self.results.append(row_dict)
                cid_close = fig.canvas.mpl_connect('close_event', on_close_ica_fig)

                # Show the figure in a blocking way so user can interact
                plt.show(block=True)

        else:
            # ===================================================================
            #                        EEG/MEG mode 
            # ===================================================================
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

            for trial_idx, trial_file in enumerate(file_paths, start=1):
                trial_start_time = time.time() - self.global_start_time

                with open(trial_file, 'rb') as f:
                    trial_dict = pickle.load(f)
                trial_data = trial_dict["data"]
                bad_channels_in_display = trial_dict["bad_chans_in_display"]
                channel_type = trial_dict.get("channel_type", "Unknown")

                n_channels = trial_data.info['nchan']
                selected_channels = set()

                print(f"[EEG/MEG Mode] Processing file: {os.path.basename(trial_file)} (Trial {trial_idx})")
                print(f"Bad channels in display: {bad_channels_in_display}")

                def on_pick(event):
                    artist = event.artist
                    if isinstance(artist, plt.Text):
                        ch_name = artist.get_text()
                        ch_names = trial_data.info['ch_names']
                        if ch_name in ch_names:
                            if ch_name in selected_channels:
                                if deselect:
                                    selected_channels.remove(ch_name)
                                    if feedback:
                                        is_correct = (ch_name not in bad_channels_in_display)
                                        FeedbackWindow(self.window, is_correct)
                            else:
                                selected_channels.add(ch_name)
                                if feedback:
                                    is_correct = (ch_name in bad_channels_in_display)
                                    FeedbackWindow(self.window, is_correct)

                def end_trial():
                    fig.canvas.mpl_disconnect(cid_pick)
                    fig.canvas.mpl_disconnect(cid_key)
                    fig.canvas.mpl_disconnect(cid_close)
                    plt.close(fig)

                    print(selected_channels)
                    hits = len(set(bad_channels_in_display) & selected_channels)
                    false_alarms = len(selected_channels - set(bad_channels_in_display))
                    misses = len(set(bad_channels_in_display) - selected_channels)
                    correct_rejections = n_channels - len(selected_channels | set(bad_channels_in_display))

                    accuracy = (hits + correct_rejections) / \
                               (hits + false_alarms + misses + correct_rejections) \
                               if (hits + false_alarms + misses + correct_rejections) > 0 else 0
                    dprime = compute_dprime(hits, false_alarms, misses, correct_rejections)

                    # if feedback:
                    messagebox.showinfo(
                        "Trial Feedback",
                        f"Trial {trial_idx} ended!\n\n"
                        f"Hits: {hits}\nFalse Alarms: {false_alarms}\n"
                        f"Misses: {misses}\nCorrect Rejections: {correct_rejections}\n"
                        f"Accuracy: {accuracy*100:.1f}%\nD-prime: {dprime:.3f}"
                    )

                    # Update line chart
                    #self.trial_result_window.update_accuracy(trial_idx, accuracy)
                    self._update_accuracy_safely(trial_idx, accuracy)

                    # Store
                    trial_end_time = time.time() - self.global_start_time
                    row_dict = {
                        'Trial': trial_idx,
                        'StartTime_s': trial_start_time,
                        'EndTime_s': trial_end_time,
                        'ChannelType': channel_type,
                        'SelectedChannels': ",".join(sorted(selected_channels)),
                        'BadChannels': ",".join(sorted(bad_channels_in_display)),
                        'Hits': hits,
                        'FalseAlarms': false_alarms,
                        'Misses': misses,
                        'CorrectRejections': correct_rejections,
                        'Accuracy': accuracy,
                        'Dprime': dprime
                    }
                    self.results.append(row_dict)

                def on_key(event):
                    if event.key == 'tab':
                        end_trial()

                def on_close(event):
                    end_trial()

                fig = trial_data.plot(
                    n_channels=n_channels,
                    duration=2,
                    block=False,
                    title=f"Trial {trial_idx} - {channel_type}"
                )
                cid_pick = fig.canvas.mpl_connect('pick_event', on_pick)
                cid_key = fig.canvas.mpl_connect('key_press_event', on_key)
                cid_close = fig.canvas.mpl_connect('close_event', on_close)

                plt.show(block=True)

        # After all trials, save CSV
        output_csv = f"results_{participant_number}_{session_number}_{experience_level}_{'exp' if feedback else 'ctrl'}.csv"
        fieldnames = [
            'Trial', 'StartTime_s', 'EndTime_s', 'ChannelType',
            'SelectedChannels', 'BadChannels',
            'Hits', 'FalseAlarms', 'Misses', 'CorrectRejections',
            'Accuracy', 'Dprime'
        ]
        with open(output_csv, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row_data in self.results:
                writer.writerow(row_data)

        print("Experiment completed. Results saved to:", output_csv)

        self.show_final_report(self.results)

    def show_final_report(self, results):
        """
        Display a final pop-up summarizing metrics across all trials, including d-prime.
        """
        # Closing the trial by trial results
        if self.trial_result_window is not None:
            if self.trial_result_window.master.winfo_exists():
                self.trial_result_window.master.destroy()
            self.trial_result_window = None  # To avoid accidentally reusing it
    
        report_window = tk.Toplevel()
        report_window.title("Final Report")
        report_window.configure(bg="white")

        self.open_windows.append(report_window)
        report_window.protocol("WM_DELETE_WINDOW", self.close_all_windows)

        # Summaries by channel type
        metrics_by_type = {}
        for row in results:
            ctype = row['ChannelType']
            h = row['Hits']
            fa = row['FalseAlarms']
            m = row['Misses']
            cr = row['CorrectRejections']
            if ctype not in metrics_by_type:
                metrics_by_type[ctype] = {
                    'hits': 0, 'fa': 0, 'miss': 0, 'cr': 0, 'count': 0
                }
            metrics_by_type[ctype]['hits'] += h
            metrics_by_type[ctype]['fa'] += fa
            metrics_by_type[ctype]['miss'] += m
            metrics_by_type[ctype]['cr'] += cr
            metrics_by_type[ctype]['count'] += 1

        lines = []
        for ctype, data in metrics_by_type.items():
            hits = data['hits']
            fa = data['fa']
            misses = data['miss']
            cr = data['cr']
            denom = hits + fa + misses + cr
            accuracy = (hits + cr) / denom if denom > 0 else 0
            dprime_val = compute_dprime(hits, fa, misses, cr)
            lines.append(
                f"Type={ctype}, Trials={data['count']} => "
                f"Hits={hits}, FA={fa}, Misses={misses}, CR={cr}, "
                f"Acc={accuracy*100:.1f}%, d'={dprime_val:.3f}"
            )

        summary_label = tk.Label(report_window, text="\n".join(lines), bg="white", justify="left")
        summary_label.pack(padx=10, pady=10)

        # Overall
        total_hits = sum(d['hits'] for d in metrics_by_type.values())
        total_fa = sum(d['fa'] for d in metrics_by_type.values())
        total_misses = sum(d['miss'] for d in metrics_by_type.values())
        total_cr = sum(d['cr'] for d in metrics_by_type.values())
        total_denom = total_hits + total_fa + total_misses + total_cr
        overall_acc = (total_hits + total_cr) / total_denom if total_denom > 0 else 0
        overall_dprime = compute_dprime(total_hits, total_fa, total_misses, total_cr)

        overall_text = (
            f"Overall => Hits={total_hits}, FA={total_fa}, Misses={total_misses}, CR={total_cr}\n"
            f"Acc={overall_acc*100:.1f}%, d'={overall_dprime:.3f}"
        )
        overall_label = tk.Label(report_window, text=overall_text, bg="white", justify="left")
        overall_label.pack(padx=10, pady=10)

        ## PLOTTING
        # 1) Group data by ctype, store (trial_num, accuracy)
        ctype2points = {} 
        overall_points = [] 

        for row in results:
            trial_idx = row['Trial']
            ctype = row['ChannelType']
            hits = row['Hits']
            fa   = row['FalseAlarms']
            miss = row['Misses']
            cr   = row['CorrectRejections']
            denom = hits + fa + miss + cr
            acc = (hits + cr)/denom if denom>0 else 0.0

            if ctype not in ctype2points:
                ctype2points[ctype] = []
            ctype2points[ctype].append((trial_idx, acc))

            overall_points.append((trial_idx, acc))

        for ctype, ptlist in ctype2points.items():
            ptlist.sort(key=lambda tup: tup[0])  # sort by trial_idx
        overall_points.sort(key=lambda tup: tup[0])

        # 2) Create subplots inside the final report window
        nrows = len(ctype2points) + 1
        fig = Figure(figsize=(6, 3*nrows), dpi=100)
        axes = fig.subplots(nrows=nrows, ncols=1)

        if nrows == 1:
            axes = [axes]  # if there's only 1 ctype, subplots returns a single Axes
        
        # 3) color cycle
        color_cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']

        ctype_list = list(ctype2points.keys())  # ['eeg','mag','grad'] in random order
        for i, ctype in enumerate(ctype_list):
            ax = axes[i]
            ax.set_title(f"{ctype} Trial-by-Trial Accuracy")
            ax.set_xlabel("Trial #")
            ax.set_ylabel("Accuracy")
            ax.set_ylim(0, 1.05)
            ax.grid(True)

            # get the data
            ptlist = ctype2points[ctype]
            xvals = [p[0] for p in ptlist]
            yvals = [p[1] for p in ptlist]
            color = color_cycle[i % len(color_cycle)]
            ax.plot(xvals, yvals, marker='o', linestyle='-', color=color)
        
        # 4) Overall in the last axis
        ax_overall = axes[-1]
        ax_overall.set_title("Overall Accuracy")
        ax_overall.set_xlabel("Trial #")
        ax_overall.set_ylabel("Accuracy")
        ax_overall.set_ylim(0, 1.05)
        ax_overall.grid(True)
        ox = [p[0] for p in overall_points]
        oy = [p[1] for p in overall_points]
        ax_overall.plot(ox, oy, marker='x', linestyle='--', color='black')

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=report_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

        # close button so that we can ensure close safely
        close_button = tk.Button(report_window, text="Close", command=self.close_all_windows)
        close_button.pack(pady=10)

    def close_all_windows(self):
        """
        Gracefully close all open windows and quit like a winner without force quitting
        """                       
        # 1) Destroy all Toplevel windows (child windows)
        for w in self.open_windows:
            try:
                if w.winfo_exists():
                    w.destroy()
            except:
                pass
        self.open_windows.clear()

        # 2) Finally destroy the main window (self.window) if it still exists
        try:
            if self.window and self.window.winfo_exists():
                self.window.quit()
                self.window.destroy()
        except:
            pass

    def _update_accuracy_safely(self, trial_idx, accuracy):
        self.trial_accuracies.append(accuracy)
        try:
            # If the root was destroyed, this call might fail
            if (not self.trial_result_window) or (not self.trial_result_window.master.winfo_exists()):
                print("Re-creating the trial result window because it was closed")
                self.trial_result_window = TrialResultWindow(master=self.window)
                self.open_windows.append(self.trial_result_window.master)
        except tk.TclError:
            print("Main app is destroyed, skipping update_accuracy_safely")
            return

        self.trial_result_window.set_accuracies(self.trial_accuracies)
# ----------------------- Main ----------------------
if __name__ == "__main__":
    app = MEG_Chicken()
    app.window.mainloop()
