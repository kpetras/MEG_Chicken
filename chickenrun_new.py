import os
import numpy as np
import mne
import tkinter as tk
from tkinter import messagebox
import pickle
import csv
import sys
import matplotlib.pyplot as plt
from slides import display_slides
from ica_plot import custome_ica_plot
import matplotlib
mne.viz.set_browser_backend('matplotlib')
matplotlib.use('tkagg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ScoreboardWindow:
    """
    A black background on-top window to report Score
      - correct_picks / total_picks
      - Accuracy
    """

    def __init__(self, master=None, parent_exp=None):
        # master should be external root
        self.master = master if master else tk.Tk()
        self.parent_exp = parent_exp
        # Toplevel
        self.win = tk.Toplevel(self.master)
        self.win.title("Scoreboard")
        self.win.configure(bg="black")
        self.win.attributes("-topmost", True)  # Set on top

        if self.parent_exp:
            self.parent_exp.open_windows.append(self.win)

        # ============ pick-level Label ============
        self.pick_feedback_label = tk.Label(
            self.win,
            text="",
            fg="white",
            bg="black",
            font=("Arial", 24, "bold")
        )
        self.pick_feedback_label.pack(padx=20, pady=10)
        
        # ============ trial-level Label ============
        self.trial_feedback_label = tk.Label(
            self.win,
            text="(No Trial Feedback Yet)",
            fg="white",
            bg="black",
            font=("Arial", 14)
        )
        self.trial_feedback_label.pack(padx=20, pady=10)
    
    def show_pick_feedback(self, is_correct: bool):
        """
        Feedback when picked
        """
        if is_correct:
            self.pick_feedback_label.config(text="CORRECT", fg="green")
        else:
            self.pick_feedback_label.config(text="INCORRECT", fg="red")

        # reset after
        self.after_id = self.win.after(2000, lambda: self.pick_feedback_label.config(text="", fg="white"))

    def update_trial_feedback(self, hits, false_alarms, misses, correct_rejections):
        """
        Trial feedback
        """
        msg = (
            f"Trial Feedback:\n"
            f"Hits = {hits}\n"
            f"False Alarms = {false_alarms}\n"
            f"Misses = {misses}\n"
            f"Correct Rejections = {correct_rejections}"
        )
        self.trial_feedback_label.config(text=msg)
    def close(self):
        """
        Close when experiment ends
        """
        if hasattr(self, 'after_id') and self.after_id:
            self.win.after_cancel(self.after_id)
        self.win.destroy()

class GamifiedEEGExp:
    def __init__(self):
        """
        Initialize tk, and show setting panel
        """
        self.window = tk.Tk()
        self.window.title("Participant Information")
        
        # Initialize result log
        self.results = []

        # Register all opened windows
        self.open_windows = []

        # UI for settings
        self.participant_number_entry = self.create_label_entry(self.window, "Participant Number:", 0)
        self.experience_level_entry = self.create_label_entry(self.window, "Experience Level \n (1-4, from very experienced to fully naïve):", 1)
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
        """
        Run experiment when submit information
        """
        participant_number = self.participant_number_entry.get()
        experience_level = self.experience_level_entry.get()
        session_number = self.session_number_entry.get()
        feedback = self.feedback_var.get()
        show_instruc = self.show_instruc_var.get()
        deselect = self.deselect_var.get()
        mode_ica = (self.mode_var.get() == "ICA")

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

        # Show instructions
        if show_instruc:
            self.show_instructions()
            slide_folder = 'slides'
            if os.path.exists(slide_folder):
                display_slides(slide_folder, master=self.window)

        # Pick channel types
        selected_channel_types = []
        if self.eeg_var.get():
            selected_channel_types.append("eeg")
        if self.mag_var.get():
            selected_channel_types.append("mag")
        if self.grad_var.get():
            selected_channel_types.append("grad")
        if not selected_channel_types:
            selected_channel_types = ["eeg", "mag", "grad"]

        # Close setting panel
        self.window.withdraw()

        # Run experiment
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

    def run_experiment(self,
                       participant_number, 
                       experience_level, 
                       session_number, 
                       feedback=True, 
                       n_trials=1, 
                       mode_ica=True, 
                       deselect=False,
                       channel_types=None):
        
        # Initialize scoreboard
        self.scoreboard = ScoreboardWindow(master=self.window, parent_exp=self)
        
        if channel_types is None:
            channel_types = ["eeg", "mag", "grad"]

        # ============= EEG/MEG mode =============
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
                print(bad_channels_in_display)

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
                    is_correct = None
                    if isinstance(artist, plt.Text):
                        ch_name = artist.get_text()
                        ch_names = trial_data.info['ch_names']
                        if ch_name in ch_names:
                            if ch_name in shared['selected_channels']:
                                if deselect:
                                    # if deselect is allowed, remove selection
                                    shared['selected_channels'].remove(ch_name)
                                    is_correct = (True if ch_name not in bad_channels_in_display else False)
                                    if feedback:
                                        self.scoreboard.show_pick_feedback(is_correct)
                                else:
                                    # if deselect it not allowed, the channel is still selected with no feed back
                                    pass
                            else:
                                shared['selected_channels'].add(ch_name)
                                is_correct = (True if ch_name in bad_channels_in_display else False)                            
                                if feedback:
                                    self.scoreboard.show_pick_feedback(is_correct)
                            
                def end_trial():
                    # Finish the trial
                    fig.canvas.mpl_disconnect(cid_pick)
                    fig.canvas.mpl_disconnect(cid_key)
                    fig.canvas.mpl_disconnect(cid_close)
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
                        self.scoreboard.update_trial_feedback(
                            hits, false_alarms, misses, correct_rejections
                        )

                    plt.close('all')

                def on_key(event):
                    if event.key == 'tab':
                        end_trial()

                def on_close(event):
                    end_trial()

                fig = trial_data.plot(
                    n_channels=n_channels,
                    duration=2,
                    block=False,
                    title=f"Trial {count}/{n_trials} - {channel_type}"
                )

                cid_pick = fig.canvas.mpl_connect('pick_event', on_pick)
                cid_key = fig.canvas.mpl_connect('key_press_event', on_key)
                cid_close = fig.canvas.mpl_connect('close_event', on_close)

                plt.show(block=True)

                trial_results = {
                    'channel_type': channel_type,
                    'hits': shared.get('hits', 0),
                    'false_alarms': shared.get('false_alarms', 0),
                    'misses': shared.get('misses', 0),
                    'correct_rejections': shared.get('correct_rejections', 0)
                }
                self.results.append(trial_results)
        
        # ============= ICA =============
        # else:
        #     data_path = os.path.join('data', 'ica')

        #     all_ica_files = []
        #     for ch_type in channel_types:
        #         ch_dir = os.path.join(data_path, ch_type)
        #         if not os.path.isdir(ch_dir):
        #             print(f"Warning: {ch_dir} not found or not a directory.")
        #             continue
                
        #         files_in_ch_dir = [f for f in os.listdir(ch_dir) if f.endswith('_ica.fif')]
        #         for ica_file in files_in_ch_dir:
        #             full_path = os.path.join(ch_dir, ica_file)
        #             all_ica_files.append((ch_type, full_path))
            
        #     if len(all_ica_files) == 0:
        #         print("No ICA files found for the specified channel_types.")
        #         return

        #     selected_ica = random.sample(all_ica_files, min(n_trials, len(all_ica_files)))

        #     with open('config.json', 'r') as file:
        #         config_data = json.load(file)
        #     ica_remove = config_data.get("ICA_remove_inds", {})

        #     for count, (ch_type, ica_path) in enumerate(selected_ica, start=1):
        #         ica_filename = os.path.basename(ica_path)
        #         print(f"Processing ICA file: {ica_filename} (Trial {count}/{n_trials}), channel_type={ch_type}")

        #         subj, ses, run = ica_filename.split('_')[:3]
        #         run_ind = run + '.fif'

        #         ica = mne.preprocessing.read_ica(ica_path)

        #         raw_file_name = subj + '_' + ses + '_' + run + '_preprocessed_raw.fif'
        #         raw_file_path = os.path.join('data', 'preprocessed', raw_file_name)
        #         raw_preprocessed = mne.io.read_raw_fif(raw_file_path, preload=True, allow_maxshield=True)

        #         ica_remove_inds_list = ica_remove[subj][run_ind][ch_type]

        #         shared = {
        #             'hits': 0,
        #             'false_alarms': 0,
        #             'misses': 0,
        #             'correct_rejections': 0,
        #             'previous_exclude': set(ica.exclude)
        #         }

        #         n_components = len(ica.get_components())
        #         fig = custome_ica_plot(
        #             ica,
        #             ica_remove_inds_list,
        #             feedback,
        #             deselect,
        #             nrows=5,
        #             ncols=10,
        #             inst=raw_preprocessed
        #         )

        #         def on_close(event):
        #             fig.canvas.mpl_disconnect(cid_close)
        #             plt.close(fig)

        #             selected = set(ica.exclude)
        #             hits = len(selected & set(ica_remove_inds_list))
        #             false_alarms = len(selected - set(ica_remove_inds_list))
        #             misses = len(set(ica_remove_inds_list) - selected)
        #             correct_rejections = n_components - len(selected | set(ica_remove_inds_list))

        #             shared['hits'] = hits
        #             shared['false_alarms'] = false_alarms
        #             shared['misses'] = misses
        #             shared['correct_rejections'] = correct_rejections

        #             if feedback:
        #                 messagebox.showinfo(
        #                     "Feedback",
        #                     f"channel_type: {ch_type}\n\n"
        #                     f"Hits: {hits}\n"
        #                     f"False Alarms: {false_alarms}\n"
        #                     f"Misses: {misses}\n"
        #                     f"Correct Rejections: {correct_rejections}"
        #                 )

        #             plt.close('all')

        #             # 也可在ICA场景下处理 scoreboard 的更新（这里省略 pick->scoreboard 的逻辑，
        #             # 因为要对ICA成分进行 pick，在你自定义的custome_ica_plot里加即可）

        #             # 记录当前准确率
        #             cur_acc = 0
        #             if self.scoreboard.total_picks > 0:
        #                 cur_acc = self.scoreboard.correct_picks / self.scoreboard.total_picks
        #             self.accuracy_history.append(cur_acc)

        #         cid_close = fig.canvas.mpl_connect('close_event', on_close)
        #         plt.show(block=True)

        #         trial_results = {
        #             'channel_type': ch_type,
        #             'hits': shared.get('hits', 0),
        #             'false_alarms': shared.get('false_alarms', 0),
        #             'misses': shared.get('misses', 0),
        #             'correct_rejections': shared.get('correct_rejections', 0)
        #         }
        #         results.append(trial_results)

        # ============= Save when finished all trials =============
        output_filename = f"results_{participant_number}_{session_number}_{experience_level}_{'exp' if feedback else 'ctrl'}.csv"
        with open(output_filename, 'w', newline='') as csvfile:
            fieldnames = ['Trial', 'channel_type', 'Hits', 'False Alarms', 'Misses', 'Correct Rejections']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for i, trial_result in enumerate(self.results, start=1):
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

        # When all trials end -> Close scoreboard -> Show final report
        self.scoreboard.close()
        # self.close_all_windows()
        self.show_final_report(self.results)

    def show_final_report(self, results):
        """
        Final report
        """
        report_window = tk.Toplevel()
        report_window.title("Final Report")
        report_window.configure(bg="white")

        # Prevent accidental window closing
        self.open_windows.append(report_window)
        report_window.protocol("WM_DELETE_WINDOW", self.close_all_windows)

        metrics_by_type = {}
        for trial_res in results:
            ctype = trial_res.get('channel_type', 'Unknown')
            h = trial_res['hits']
            fa = trial_res['false_alarms']
            m = trial_res['misses']
            cr = trial_res['correct_rejections']
            if ctype not in metrics_by_type:
                metrics_by_type[ctype] = {'hits': 0, 'false_alarms': 0, 'misses': 0, 'correct_rejections': 0, 'count': 0}
            metrics_by_type[ctype]['hits'] += h
            metrics_by_type[ctype]['false_alarms'] += fa
            metrics_by_type[ctype]['misses'] += m
            metrics_by_type[ctype]['correct_rejections'] += cr
            metrics_by_type[ctype]['count'] += 1

        lines = []
        for ctype, data in metrics_by_type.items():
            hits = data['hits']
            fa = data['false_alarms']
            misses = data['misses']
            cr = data['correct_rejections']

            denom = hits + fa + misses + cr  # Total channels
            if denom > 0:
                accuracy = (hits + cr) / denom
            else:
                accuracy = 0.0

            # Precision / Recall / F1
            precision = hits / (hits + fa + 1e-9)
            recall = hits / (hits + misses + 1e-9)
            f1 = 2 * precision * recall / (precision + recall + 1e-9)

            lines.append(
                f"Type={ctype}  Trials={data['count']}  "
                f"Hits={hits}, FA={fa}, Misses={misses}, CR={cr},  "
                f"Acc={accuracy*100:.1f}%, P={precision:.2f}, R={recall:.2f}, F1={f1:.2f}"
            )

        # Display the final summary
        summary_label = tk.Label(report_window, text="\n".join(lines), bg="white", justify="left")
        summary_label.pack(padx=10, pady=10)

        # Display overall accuracy
        total_hits, total_fa, total_misses, total_cr = 0, 0, 0, 0
        for data in metrics_by_type.values():
            total_hits += data['hits']
            total_fa += data['false_alarms']
            total_misses += data['misses']
            total_cr += data['correct_rejections']

        total_denom = total_hits + total_fa + total_misses + total_cr
        if total_denom > 0:
            overall_acc = (total_hits + total_cr) / total_denom
        else:
            overall_acc = 0.0

        overall_precision = total_hits / (total_hits + total_fa + 1e-9)
        overall_recall = total_hits / (total_hits + total_misses + 1e-9)
        overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall + 1e-9)

        overall_line = (
            f"Overall: Hits={total_hits}, FA={total_fa}, Misses={total_misses}, CR={total_cr}, "
            f"Acc={overall_acc*100:.1f}%, P={overall_precision:.2f}, R={overall_recall:.2f}, F1={overall_f1:.2f}"
        )
        overall_label = tk.Label(report_window, text=overall_line, bg="white", justify="left")
        overall_label.pack(padx=10, pady=10)

        # Add a close button
        close_button = tk.Button(report_window, text="Close", command=self.close_all_windows)
        close_button.pack(pady=10)

        self.plot_trial_by_trial(results, report_window)

    
    def plot_trial_by_trial(self, results, parent_window):
        """
        Plots trial-by-trial performance metrics.
        """
        hits = [result['hits'] for result in results]
        false_alarms = [result['false_alarms'] for result in results]
        misses = [result['misses'] for result in results]
        correct_rejections = [result['correct_rejections'] for result in results]

        accuracy = [
            (h + cr) / (h + fa + m + cr) if (h + fa + m + cr) > 0 else 0
            for h, fa, m, cr in zip(hits, false_alarms, misses, correct_rejections)
        ]

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(range(1, len(accuracy) + 1), accuracy, marker='o', linestyle='-', color='b')
        ax.set_xlabel('Trial Number')
        ax.set_ylabel('Accuracy')
        ax.set_title('Trial-by-Trial Accuracy')
        ax.grid(True)

        canvas = FigureCanvasTkAgg(fig, master=parent_window)
        canvas.draw()
        canvas.get_tk_widget().pack(padx=10, pady=10)

    def close_all_windows(self):
        """
        Close all open windows and quit the application safely.
        """
        for window in self.open_windows:
            if hasattr(window, 'after_id') and window.after_id:
                window.after_cancel(window.after_id)
            if window.winfo_exists():
                window.destroy()

        if self.window.winfo_exists():
            self.window.quit()  # Stop the main event loop
            self.window.destroy()  # Destroy the main window
# ----------------------- Main -----------------------
if __name__ == "__main__":
    app = GamifiedEEGExp()
    app.window.mainloop()
