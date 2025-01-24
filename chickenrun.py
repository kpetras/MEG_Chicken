import os
import time
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
import config
import run_funcs
from ica_plot import custome_ica_plot
from FeedbackWindow import FeedbackWindow, TrialResultWindow, TrialEndWindow
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

class MEG_Chicken:
    def __init__(self):
        """ The main window for collecting participant info. """
        self.window = tk.Tk()
        self.window.title("Participant Information")

        self.open_windows = [] # To register the opened windows so that we can actually close them all...
        self.results = []  # store trial-wise dict
        self.trial_accuracies = []

        # Flag for user decision to Save & Quit mid-experiment
        self.user_wants_to_quit = False

        # for overall timing, not sure if im using this since we now have save and quit
        self.global_start_time = None 

        # UI for participant settings
        self.participant_number_entry = self.create_label_entry(self.window, "Participant Number:", 0)
        # Maybe we can do something? but not now
        # self.experience_level_entry = self.create_label_entry(self.window, "Experience Level (1-4):", 1)
        self.session_number_entry = self.create_label_entry(self.window, "Session Number:", 1)

        self.feedback_var = tk.BooleanVar(value=False)
        feedback_checkbox = tk.Checkbutton(self.window, text="Enable Immediate Feedback", variable=self.feedback_var)
        feedback_checkbox.grid(row=3, column=1, columnspan=2, sticky="w")

        self.show_instruc_var = tk.BooleanVar(value=False)
        instruc_checkbox = tk.Checkbutton(self.window, text="Show Instruction", variable=self.show_instruc_var)
        instruc_checkbox.grid(row=4, column=1, columnspan=2, sticky="w")

        self.deselect_var = tk.BooleanVar(value=False)
        deselect_checkbox = tk.Checkbutton(self.window, text="Enable Deselect", variable=self.deselect_var)
        deselect_checkbox.grid(row=5, column=1, columnspan=2, sticky="w")

        self.mode_var = tk.StringVar(value="EEG/MEG")
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
        # experience_level = self.experience_level_entry.get()
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
        # if not experience_level.isdigit() or not (1 <= int(experience_level) <= 4):
        #     messagebox.showerror("Invalid Input", "Experience level must be 1 ~ 4.")
        #     return

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
            # experience_level,
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
                    #    experience_level,
                       session_number,
                       feedback=True,
                       n_trials=config.n_trials_per_session,
                       mode_ica=True,
                       deselect=False,
                       channel_types=None):
        """
        Output: 
        1. trial results in CSV.
        2. Experiment response time in CSV
        3. Run the rest of the trial if session is created but not completed
        4. Allowing to Save and Quit mid-session and resume next time
        """
        if channel_types is None:
            channel_types = ["eeg", "mag", "grad"]

        session_id = f"{participant_number}_{session_number}"
        session_dir = config.session_dir
        os.makedirs(session_dir, exist_ok=True)
        session_file_path = os.path.join(session_dir, f"{session_id}_{'ICA' if mode_ica else 'MEEG'}.pkl")
        
        os.makedirs(config.res_dir, exist_ok=True)
        output_csv = os.path.join(
            config.res_dir,
            f"results_{participant_number}_{session_number}_{'ICA' if mode_ica else 'MEEG'}_{'exp' if feedback else 'ctrl'}.csv"
        )

        completed_trial_ids = set()
        if os.path.exists(output_csv):
            with open(output_csv, "r", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        row["Trial"] = int(row["Trial"])
                    except ValueError:
                        continue
                    for num_field in ["Hits","FalseAlarms","Misses","CorrectRejections"]:
                        if num_field in row:
                            row[num_field] = int(row[num_field])
                    for float_field in ["StartTime_s","EndTime_s","Accuracy"]:
                        if float_field in row:
                            row[float_field] = float(row[float_field])

                    completed_trial_ids.add(row["Trial"])                    
                    # Store the row in self.results
                    self.results.append(row)
                    if "Accuracy" in row:
                        self.trial_accuracies.append(row["Accuracy"])

        # If no file exist for corresponding session id, we create one 
        if not os.path.exists(session_file_path):
            trials_list = []
            if mode_ica:
                data_path = config.ica_dir
                all_files = run_funcs.collect_files(data_path, channel_types, '_ica.fif', 'ICA')
                if all_files is None:
                    return
                trials_list = run_funcs.process_trial_files(all_files, n_trials, 'ICA', data_path)
            
            else:
                data_path = config.trials_dir
                all_files = run_funcs.collect_files(data_path, channel_types, '.pkl', 'MEEG')
                if all_files is None:
                    return
                trials_list = run_funcs.process_trial_files(all_files, n_trials, 'MEEG', data_path)
            
            # Save session file
            with open(session_file_path, "wb") as f_pkl:
                pickle.dump(trials_list, f_pkl)
            print(f"Session file created: {session_file_path}, total trials={len(trials_list)}")
        else:
            # If exist, load
            with open(session_file_path, "rb") as f_pkl:
                trials_list = pickle.load(f_pkl)
            print(f"Session file found. Total trials in session file: {len(trials_list)}")

        # 4) Filter out the completed trials
        remaining_trials = [t for t in trials_list if t["Trial"] not in completed_trial_ids]
        print("num remaining_trials", len(remaining_trials))
        print("completed_trial_ids", completed_trial_ids)
        if len(remaining_trials) == 0:
            messagebox.showinfo("All Trials Done", "All trials have been completed for this session!")
            self._close_all_windows() 
            return        
                
        # Initialize the always-open trial result window to show default instruction
        self.trial_result_window = TrialResultWindow(master=self.window)
        self.open_windows.append(self.trial_result_window.master)

        for trial_idx, trial_info in enumerate(remaining_trials, start= len(completed_trial_ids) + 1):
            print(trial_idx)
            if self.user_wants_to_quit:
                break

            if trial_info["mode"] == "ICA":
            # =======================================================
            #                    ICA mode 
            # =======================================================
                ch_type = trial_info["ch_type"]
                ica_filename = os.path.basename(trial_info["trial_path"])
                print(f"[ICA] Trial {trial_idx}/{config.n_trials_per_session} => {ica_filename} (ch={ch_type})")

                name_split = ica_filename.split('_')
                try:
                    subj, ses, run = name_split[0], name_split[1], name_split[2]
                except IndexError:
                    subj, ses, run = "unknown_subj", "unknown_ses", "unknown_run"

                ica = mne.preprocessing.read_ica(trial_info["trial_path"])

                raw_file_name = f"{subj}_{ses}_{run}_preprocessed_raw.fif"
                raw_file_path = os.path.join(config.preprocessed_save_path, raw_file_name)
                if not os.path.exists(raw_file_path):
                    print(f"Cannot find {raw_file_path}. Skipping trial.")
                    continue
                raw_preprocessed = mne.io.read_raw_fif(raw_file_path, preload=True, allow_maxshield=True)

                # Answers
                ica_remove = {}
                answer_dir = config.answer_dir
                answer_data_file = 'answer_standardized.json'
                answer_data_path = os.path.join(answer_dir, answer_data_file)
                if os.path.exists(answer_data_path):
                    with open(answer_data_path, 'r') as file:
                        answer_data = json.load(file)
                    ica_remove = answer_data.get("ICA_remove_inds", {})
                bad_components = []
                if (subj in ica_remove) and (ses in ica_remove[subj]) and (run in ica_remove[subj][ses]) and (ch_type in ica_remove[subj][ses][run]):
                    bad_components = ica_remove[subj][ses][run][ch_type]
                
                print(bad_components)

                fig = custome_ica_plot(
                    ica,
                    ICA_remove_inds_list=bad_components,
                    feedback=feedback,
                    deselect=deselect,
                    inst=raw_preprocessed,
                    nrows=5,
                    ncols=10,
                    master=self.window,
                    title=f"Trial {trial_idx} - {ch_type}"
                )

                # Trial start time after plotting since it takes some time to initialize
                # Not exactly sure to use real time or interval
                trial_start_time = time.time()

                selected_comps = set()

                def on_close_ica_fig(event):
                    """When the ICA figure is closed, finalize the trial metrics."""
                    trial_end_time = time.time()
                    fig.canvas.mpl_disconnect(cid_close)
                    plt.close(fig)

                    selected_comps.update(ica.exclude)
                    hits = len(set(bad_components) & selected_comps)
                    false_alarms = len(selected_comps - set(bad_components))
                    misses = len(set(bad_components) - selected_comps)
                    n_components = config.ica_components
                    correct_rejections = n_components - len(set(bad_components) | selected_comps)

                    denom = hits + false_alarms + misses + correct_rejections
                    accuracy = (hits + correct_rejections) / denom if denom > 0 else 0

                    summary_window = TrialEndWindow(
                    master=self.window,
                    trial_idx=trial_idx,
                    hits=hits,
                    false_alarms=false_alarms,
                    misses=misses,
                    correct_rejections=correct_rejections
                    )
                    if summary_window.user_wants_quit:
                        self.user_wants_to_quit = True
                    
                    self._update_accuracy_safely(trial_idx, accuracy)

                    
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
                        'Accuracy': accuracy
                    }
                    self._append_result_to_csv(row_dict, output_csv)

                cid_close = fig.canvas.mpl_connect('close_event', on_close_ica_fig)

                plt.show(block=True)

            else:
                # ===================================================================
                #                        MEEG mode 
                # ===================================================================
                file_path = trial_info["trial_path"]
                print(file_path)
                with open(file_path, 'rb') as f:
                    tdict = pickle.load(f)
                trial_data = tdict["data"]
                bad_channels_in_display = tdict["bad_chans_in_display"]
                channel_type = tdict.get("channel_type", "Unknown")

                n_channels = trial_data.info['nchan']
                selected_channels = set()

                print(f"[EEG/MEG] Trial {trial_idx}/{config.n_trials_per_session} => {os.path.basename(file_path)}")
                trial_start_time = time.time()

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

                    hits = len(set(bad_channels_in_display) & selected_channels)
                    false_alarms = len(selected_channels - set(bad_channels_in_display))
                    misses = len(set(bad_channels_in_display) - selected_channels)
                    correct_rejections = n_channels - len(selected_channels | set(bad_channels_in_display))

                    denom = hits + false_alarms + misses + correct_rejections
                    accuracy = (hits + correct_rejections) / denom if denom > 0 else 0

                    summary_window = TrialEndWindow(
                    master=self.window,
                    trial_idx=trial_idx,
                    hits=hits,
                    false_alarms=false_alarms,
                    misses=misses,
                    correct_rejections=correct_rejections
                    )
                    if summary_window.user_wants_quit:
                        self.user_wants_to_quit = True
                    
                    self._update_accuracy_safely(trial_idx, accuracy)

                    trial_end_time = time.time()
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
                        'Accuracy': accuracy
                    }
                    self._append_result_to_csv(row_dict, output_csv)

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

            if self.user_wants_to_quit:
                break

        if not self.user_wants_to_quit:
            self.show_final_report(self.results)
        else:
            messagebox.showinfo("Session Paused", "You chose to save & quit. Next time, the remaining trials will resume.")
            self._close_all_windows()


    def _append_result_to_csv(self, row_dict, csv_path):
        """
        Append one trial row to an existing or new CSV file.
        Also store it to self.results in memory.
        """
        fieldnames = [
            'Trial', 'StartTime_s', 'EndTime_s', 'ChannelType',
            'SelectedChannels', 'BadChannels',
            'Hits', 'FalseAlarms', 'Misses', 'CorrectRejections',
            'Accuracy'
        ]
        file_existed = os.path.exists(csv_path)
        with open(csv_path, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_existed or os.path.getsize(csv_path) == 0:
                writer.writeheader()
            writer.writerow(row_dict)

        self.results.append(row_dict)


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
        report_window.protocol("WM_DELETE_WINDOW", self._close_all_windows)

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
            dprime_val = run_funcs.compute_dprime(hits, fa, misses, cr)
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
        overall_dprime = run_funcs.compute_dprime(total_hits, total_fa, total_misses, total_cr)

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

        ctype_list = list(ctype2points.keys())
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
        close_button = tk.Button(report_window, text="Close", command=self._close_all_windows)
        close_button.pack(pady=10)

    def _close_all_windows(self):
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
            if (not self.trial_result_window) or (not self.trial_result_window.master.winfo_exists()):
                print("Re-creating the trial result window because it was closed")
                self.trial_result_window = TrialResultWindow(master=self.window)
                self.open_windows.append(self.trial_result_window.master)
        except tk.TclError:
            # Most probably won't happen but who knows
            print("Main app is destroyed.")
            return

        self.trial_result_window.set_accuracies(self.trial_accuracies)
# ----------------------- Main ----------------------
if __name__ == "__main__":
    app = MEG_Chicken()
    app.window.mainloop()
