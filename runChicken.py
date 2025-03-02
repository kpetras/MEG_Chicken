# runChicken.py
import os
import time
import json
import mne
import tkinter as tk
from tkinter import messagebox, ttk, PhotoImage
import pickle
import csv
import matplotlib
import matplotlib.pyplot as plt
import warnings
import config
import random

from functools import partial
from chickencode import run_funcs
from chickencode.ica_plot import custome_ica_plot
from chickencode.FeedbackWindow import FeedbackWindow, TrialEndWindow
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
    from slides.slides import display_slides
except ImportError:
    def display_slides(*args, **kwargs):
        pass

class MEG_Chicken:
    def __init__(self):        
        self.window = tk.Tk()
        self.window.title("Participant Information")

        self.open_windows = [] # To register the opened windows so that we can actually close them all...
        self.results = []  # store trial-wise dict
        self.trial_accuracies = []

        # Flag for user decision to Save & Quit mid-experiment
        self.user_wants_to_quit = False

        # for overall timing, not sure if im using this since we now have save and quit
        self.global_start_time = None 

        # Participant Info Rows
        self.participant_number_entry = self.create_label_entry(self.window, "Participant Number:", 0)
        self.session_number_entry = self.create_label_entry(self.window, "Session Number:", 1) 
     
        self.feedback_var = tk.BooleanVar(value=False)
        feedback_checkbox = tk.Checkbutton(self.window, text="Enable Immediate Feedback", variable=self.feedback_var)
        feedback_checkbox.grid(row=4, column=1, columnspan=2, sticky="w")

        self.show_instruc_var = tk.BooleanVar(value=False)
        instruc_checkbox = tk.Checkbutton(self.window, text="Show Instruction", variable=self.show_instruc_var)
        instruc_checkbox.grid(row=5, column=1, columnspan=2, sticky="w")

        self.deselect_var = tk.BooleanVar(value=False)
        deselect_checkbox = tk.Checkbutton(self.window, text="Enable Deselect", variable=self.deselect_var)
        deselect_checkbox.grid(row=6, column=1, columnspan=2, sticky="w")

        self.mode_var = tk.StringVar(value="components")
        radio_ica = tk.Radiobutton(self.window, text="Bad independent component selection", variable=self.mode_var, value="components")
        radio_ica.grid(row=4, column=0, sticky="w")
        radio_eeg_meg = tk.Radiobutton(self.window, text="Bad Channel selection", variable=self.mode_var, value="channels")
        radio_eeg_meg.grid(row=5, column=0, sticky="w")

        self.eeg_var = tk.BooleanVar(value=True)
        cb_eeg = tk.Checkbutton(self.window, text="EEG", variable=self.eeg_var)
        cb_eeg.grid(row=7, column=0, sticky="w")

        self.mag_var = tk.BooleanVar(value=True)
        cb_mag = tk.Checkbutton(self.window, text="Mag", variable=self.mag_var)
        cb_mag.grid(row=7, column=1, sticky="w")

        self.grad_var = tk.BooleanVar(value=True)
        cb_grad = tk.Checkbutton(self.window, text="Grad", variable=self.grad_var)
        cb_grad.grid(row=7, column=2, sticky="w")

        submit_button = tk.Button(self.window, text="Submit", command=self.on_submit)
        submit_button.grid(row=8, column=0, columnspan=3)

    def create_label_entry(self, window, text, row):
        label = tk.Label(window, text=text)
        label.grid(row=row, column=0)
        entry = tk.Entry(window)
        entry.grid(row=row, column=1)
        return entry

    def on_submit(self):
        """ The main window for collecting participant info. """   
        self.base_filenames = os.listdir(config.answer_dir)
        self.base_filenames = [filename[:-5] for filename in self.base_filenames]
        #check which options can be made into trials
        self.allowed_trials = {}
        self.requested_types = []
        if self.mode_var.get() == "components":
            if self.eeg_var:
                self.requested_types.append('ICA_remove_inds_eeg')
            if self.mag_var:
                self.requested_types.append('ICA_remove_inds_mag')
            if self.grad_var:
                self.requested_types.append('ICA_remove_inds_grad')
        else:
            if self.eeg_var.get():
                self.requested_types.append('badC_EEG')
            if self.mag_var:
                self.requested_types.append('badC_MAG')
            if self.grad_var:
                self.requested_types.append('badC_GRAD')

        for basefilename in self.base_filenames:
            with open(os.path.join(config.answer_dir, basefilename + ".json"), 'r') as file:
                answer_data = json.load(file)
                self.allowed_trials[basefilename] = []
                for key in self.requested_types:
                    if answer_data[key] == []:
                        print(f"Missing indeces for {key} in answer file {basefilename}. No such trials will be added")
                    else:
                        self.allowed_trials[basefilename].append(key)
        trialfound = False
        for key in self.allowed_trials.keys():
            if self.allowed_trials[key]:
                trialfound = True
        if not trialfound:
            print("No valid answer files found, exiting.")
            return

        if self.mode_var.get() == "components":
            for basefilename in self.base_filenames:
                with open(os.path.join(config.answer_dir, basefilename + ".json"), 'r') as file:
                    answer_data = json.load(file)
                    hasnobadseeg = answer_data.get("ICA_remove_inds_eeg", []) == []               
                    hasnobadsmag = answer_data.get("ICA_remove_inds_mag", []) == []
                    hasnobadsgrad = answer_data.get("ICA_remove_inds_grad", []) == []
                data_file_found, preproc_file_found, eeg_ica_file_found, mag_ica_file_found, grad_ica_file_found = False, False, False, False, False
                for data_file in os.listdir(config.raw_dir):
                    if data_file == basefilename + ".fif":
                        data_file_found = True
                for preproc_file in os.listdir(config.preproc_dir):
                    if preproc_file == basefilename + "_preproc.fif":
                        preproc_file_found = True
                for ica_file in os.listdir(config.ica_dir + "\\eeg"):
                    if ica_file == basefilename + "_ica.fif":
                        if not hasnobadseeg:
                            eeg_ica_file_found = True
                for ica_file in os.listdir(config.ica_dir + "\\mag"):
                    if ica_file == basefilename + "_ica.fif":
                        if not hasnobadsmag:
                            mag_ica_file_found = True
                for ica_file in os.listdir(config.ica_dir + "\\grad"):
                    if ica_file == basefilename + "_ica.fif":
                        if not hasnobadsgrad:
                            grad_ica_file_found = True
                        
                if not (data_file_found and 
                        preproc_file_found and 
                        (eeg_ica_file_found or 
                        mag_ica_file_found or 
                        grad_ica_file_found)):
                    print(f"Missing files for {basefilename}. Removing from list.")
                    del self.allowed_trials[basefilename]

        else:
            for basefilename in self.base_filenames:
                with open(os.path.join(config.answer_dir, basefilename + ".json"), 'r') as file:
                    answer_data = json.load(file)

                    hasnobadchannelseeg = answer_data.get("badC_EEG", []) == []
                    hasnobadchannelsmeg = answer_data.get("badC_MEG", []) == []
                data_file_found, preproc_file_found, eeg_ica_file_found, mag_ica_file_found, grad_ica_file_found = False, False, False, False, False
                for data_file in os.listdir(config.raw_dir):
                    if data_file == basefilename + ".fif":
                        data_file_found = True
                for preproc_file in os.listdir(config.preproc_dir):
                    if preproc_file == basefilename + "_preproc.fif" and not hasnobadchannelseeg and not hasnobadchannelsmeg:
                        preproc_file_found = True               
                        
                if not data_file_found and preproc_file_found:
                    print(f"Missing files for {basefilename}. Removing from list.")
                    del self.allowed_trials[basefilename]
        #extra check to see if at least one of the requested types is in the allowed trials    
        
        for key in self.requested_types:
            keyfound = False
            for allowed_trial in self.allowed_trials.values():
                if key in allowed_trial:
                    keyfound = True                
            if not keyfound:
                self.requested_types.remove(key)
                print(f"Warning, no trials found for requested type{key}, not adding to trials")
        
        if not self.base_filenames:
            print("No valid answer files found.")
            return
        print("Submit clicked")
        self.run_trials()

    def run_trials(self):
        """ Run the trials. """
        nTrials = 20
        for trialNR in range(nTrials):
            datafile, badIndeces, datatype = self.make_next_trial()
            if self.mode_var.get() == "components":
                self.show_ica_trial( datafile, trialNR, nTrials, badIndeces, datatype)
            else:
                self.show_channel_trial( trialNR, badIndeces)

    def make_next_trial(self):
        """ Make the next trial. """
        # pick random datafile from datafiles
        
        picked_type =  random.choice(self.requested_types)       
        datafile = random.choice(list(self.allowed_trials.keys()))
        max_iter = 100
        while not picked_type in list(self.allowed_trials[datafile]) and max_iter > 0:
            datafile = random.choice(list(self.allowed_trials.keys()))
            max_iter -= 1

        if self.mode_var.get() == "components":
            
            # =======================================================
            #                    ICA mode 
            # =======================================================

            # Answers
            answer_data_path = os.path.join(config.answer_dir, datafile + ".json")
            with open(answer_data_path, 'r') as file:
                answer_data = json.load(file)
            bad_indeces = answer_data.get(picked_type, {})
        return datafile, bad_indeces, picked_type

    def show_ica_trial(self, datafile, trialNR, nTrials, bad_components, datatype):
        """ Show the trial. """
        # Load the data
        if datatype == 'ICA_remove_inds_eeg':
            ch_type_dir = 'eeg'
        elif datatype == 'ICA_remove_inds_mag':
            ch_type_dir = 'mag'
        elif datatype == 'ICA_remove_inds_grad':
            ch_type_dir = 'grad'
        full_path = os.path.join(config.ica_dir, ch_type_dir)
        ica = mne.preprocessing.read_ica(os.path.join(full_path, datafile) + "_ica.fif")
        raw_data = mne.io.read_raw_fif(os.path.join(config.raw_dir, datafile + ".fif"), preload=True)
        
        fig = custome_ica_plot(
                ica,
                ICA_remove_inds_list=bad_components,
                feedback=self.feedback_var.get(),
                deselect=self.deselect_var.get(),
                inst=raw_data,
                nrows=5,
                ncols=10,
                master=self.window,
                title=f"Trial {trialNR}/{nTrials} - {ch_type_dir}, click here to answer"
            )
        
        ica.plot_sources(title=f"Trial {trialNR}/{nTrials} - {ch_type_dir}", 
                inst = raw_data,
                show = False)

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
            missed_channels = set(bad_components) - selected_comps
            misses = len(missed_channels)
            n_components = config.ica_components
            correct_rejections = n_components - len(set(bad_components) | selected_comps)

            denom = hits + false_alarms + misses + correct_rejections
            accuracy = (hits + correct_rejections) / denom if denom > 0 else 0
            summary_window = TrialEndWindow(
            master=self.window,
            trial_idx=trialNR,
            hits=hits,
            false_alarms=false_alarms,
            misses=misses,
            correct_rejections=correct_rejections,
            missed_channels = missed_channels
            )
            if summary_window.user_wants_quit:
                self.user_wants_to_quit = True
            
            row_dict = {
                'Trial': trialNR,
                'StartTime_s': trial_start_time,
                'EndTime_s': trial_end_time,
                'ChannelType': ch_type_dir,
                'SelectedChannels': ",".join(str(x) for x in sorted(selected_comps)),
                'BadChannels': ",".join(str(x) for x in sorted(bad_components)),
                'Hits': hits,
                'FalseAlarms': false_alarms,
                'Misses': misses,
                'CorrectRejections': correct_rejections,
                'Accuracy': accuracy,
                'D-Prime': run_funcs.compute_dprime(hits, false_alarms, misses, correct_rejections)
            }
            #self._append_result_to_csv(row_dict, output_csv)

        cid_close = fig.canvas.mpl_connect('close_event', on_close_ica_fig)
        plt.show(block=True)

    def show_channel_trial(self, trial):
        """ Show the trial. """
        fig = trial_data.plot(
                            n_channels=n_channels,
                            duration=2,
                            block=False,
                            picks = chs2display,
                            title=f"Trial {trial_idx}/{n_trials} - {channel_type}"
                        )

if __name__ == "__main__":
    app = MEG_Chicken()
    app.window.mainloop()
