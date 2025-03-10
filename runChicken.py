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
import copy
import random

from functools import partial
from chickencode import run_funcs
from chickencode.ica_plot import custom_ica_plot
from chickencode.FeedbackWindows import FeedbackWindow, TrialEndWindow

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

        self.current_session = run_funcs.session_handler(
            master_window=self.window,
            mode=self.mode_var.get(),
            nTrials=nTrials,
            instantfeedback=self.feedback_var.get()
        )
        
        for trialNR in range(nTrials):
            datafile, badIndeces, datatype = self.make_next_trial()            
            if self.mode_var.get() == "components":
                self.show_ica_trial(datafile, trialNR, nTrials, badIndeces, datatype)
            elif self.mode_var.get() == "channels":
                self.show_channel_trial(datafile, trialNR, nTrials, badIndeces, datatype)

    def make_next_trial(self):
        """ Make the next trial. """
        # pick random datafile from datafiles
        
        picked_type =  random.choice(self.requested_types)       
        datafile = random.choice(list(self.allowed_trials.keys()))
        max_iter = 100
        while not picked_type in list(self.allowed_trials[datafile]) and max_iter > 0:
            datafile = random.choice(list(self.allowed_trials.keys()))
            max_iter -= 1

        answer_data_path = os.path.join(config.answer_dir, datafile + ".json")
        with open(answer_data_path, 'r') as file:
            answer_data = json.load(file)
        bad_indeces = answer_data.get(picked_type, {})        

        return datafile, bad_indeces, picked_type

    def generate_picks(self, bad_candidates, max_candidates):
        picks = []
        # Set a random amount of bad components to show              
        amount_of_bad_components = random.randint(1, len(bad_candidates))
        bad_components_to_show = []
        # Randomly select the bad components
        i = 0
        max_iter = 100
        while i < (amount_of_bad_components) and max_iter > 0:
            random_index = random.randint(0, len(bad_candidates) - 1)
            if not bad_candidates[random_index] in bad_components_to_show:
                bad_components_to_show.append(bad_candidates[random_index])
                picks.append(bad_candidates[random_index])
                i+=1
            max_iter -= 1
            if max_iter == 0:
                print("Warning, could not find enough bad components")
                break

        # fill the rest with random components
        max_iter = 100
        while not len(picks) == 10:
            random_index = random.randint(0, max_candidates - 1)
            if not random_index in picks and not random_index in bad_candidates:
                picks.append(random_index)
            max_iter -= 1
            if max_iter == 0:
                print("Warning, could not find enough random trials")
                break
            
        #shuffle the picks
        random.shuffle(picks)    
        return picks, bad_components_to_show
    
    def load_component_trial_data(self, datafile, datatype):
        if datatype == 'ICA_remove_inds_eeg':
            ch_type_dir = 'eeg'
        elif datatype == 'ICA_remove_inds_mag':
            ch_type_dir = 'mag'
        elif datatype == 'ICA_remove_inds_grad':
            ch_type_dir = 'grad'
        #Append channel dir to path and load the data	    
        full_path = os.path.join(config.ica_dir, ch_type_dir)
        ica = mne.preprocessing.read_ica(os.path.join(full_path, datafile) + "_ica.fif")
        raw_data = mne.io.read_raw_fif(os.path.join(config.raw_dir, datafile + ".fif"), preload=True)
        return ica, raw_data
    
    def load_channel_trial_data(self, datafile):
        raw_data = mne.io.read_raw_fif(os.path.join(config.preproc_dir, datafile + "_preproc.fif"), preload=True)
        return raw_data

    def show_ica_trial(self, datafile, trialNR, nTrials, bad_components, datatype):        
        # Load the data
        ica, raw_data = self.load_component_trial_data(datafile, datatype)
        # determine picks
        picks, bad_components_shown = self.generate_picks(bad_components, len(ica._ica_names))    

        self.current_session.init_next_trial( trialNR, ica._ica_names, bad_components_shown )
        fig = custom_ica_plot(
                ica,
                session=self.current_session,
                ICA_remove_inds_list=bad_components,
                feedback=self.feedback_var.get(),
                deselect=self.deselect_var.get(),
                inst=raw_data,
                picks=picks,
                nrows=5,
                ncols=10,
                master=self.window,
                title=f"Trial {trialNR}/{nTrials} - {datatype}, click here to answer"
            )            

        fig2 = ica.plot_sources(title=f"Trial {trialNR}/{nTrials} - {datatype}", 
                inst = raw_data,
                picks = picks,
                show = False)        

        self.current_session.add_windows(fig, fig2)        
        plt.show(block=True)

    def show_channel_trial(self, datafile, trialNR, nTrials, bad_channels, datatype):
        data = self.load_channel_trial_data(datafile)

        picks, bad_channels_shown = self.generate_picks(bad_channels, len(data.info['ch_names']))

        #Find channel names for the picks
        for ind, pick in enumerate(picks):
            #if type is int
            if type(pick) == int:
                picks[ind] = data.info['ch_names'][ind]        
        
        #find indeces for bad channels
        for ind, bad_channel in enumerate(bad_channels_shown):
            bad_channels_shown[ind] = data.info['ch_names'].index(bad_channel)

        self.current_session.init_next_trial(trialNR, data.info['ch_names'], bad_channels_shown)
        data.info['bads'] = []
        fig = data.plot(
                        n_channels=len(picks),
                        duration=2,
                        block=False,
                        picks = picks,
                        title=f"Trial {trialNR}/{nTrials} - {datatype}",
                        color='b',                    
                        )
        
        self.current_session.add_windows(None, fig)   
        plt.show(block=True)

if __name__ == "__main__":
    app = MEG_Chicken()
    app.window.mainloop()
