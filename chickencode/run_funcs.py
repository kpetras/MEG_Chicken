
import os
import random
from tkinter import messagebox
import json
import mne
import sqlite3
import pickle
import config
from chickencode.FeedbackWindows import FeedbackWindow, TrialEndWindow
import matplotlib.pyplot as plt
import matplotlib
# -----------------------------------------
#           Everything Calculation
# -----------------------------------------
    
def _get_dataset_config(dataset_name):
    config_file = os.path.join("data", dataset_name, "core_data", "dataset_config.json")
    if not os.path.exists(config_file):
        return None
    with open(config_file, "r") as f:
        return json.load(f)

# -----------------------------------------
#           Everything MEEG Trials
# -----------------------------------------
def load_all_meeg_trials(dataset_name, channel_types=None):
    trial_db_path = os.path.join("data", dataset_name, "core_data", "index_db", "trials.db")
    if not os.path.exists(trial_db_path):
        print(f"[ERROR] No trials.db found: {trial_db_path}")
        return []

    conn = sqlite3.connect(trial_db_path)
    cursor = conn.cursor()

    if channel_types:
        # build a parameterized IN clause
        placeholders = ",".join(["?"] * len(channel_types))
        query = f"""
        SELECT trial_id, subj, ses, run, ch_type, version, chs2display, bad_channels
        FROM trials
        WHERE ch_type IN ({placeholders})
        """
        cursor.execute(query, channel_types)
    else:
        query = """
        SELECT trial_id, subj, ses, run, ch_type, version, chs2display, bad_channels
        FROM trials
        """
        cursor.execute(query)

    rows = cursor.fetchall()
    conn.close()

    all_trials = []
    for row in rows:
        trial_info = {
            "trial_id": row[0],
            "subj": row[1],
            "ses": row[2],
            "run": row[3],
            "ch_type": row[4],
            "version": row[5],
            "chs2display": pickle.loads(row[6]),      # un-pickle
            "bad_channels": pickle.loads(row[7]),    # un-pickle
            "mode": "MEEG"
        }
        all_trials.append(trial_info)

    return all_trials

# -----------------------------------------
#           Everything ICA
# -----------------------------------------
def load_preprocessed_raw_all_channels(dataset_name, subj, ses, run):
    fif_path = os.path.join("data", dataset_name, "core_data",
                            f"{subj}_{ses}_{run}_preproc_raw.fif")
    if not os.path.exists(fif_path):
        print(f"[ERROR] Could not find .fif file: {fif_path}")
        return None
    return mne.io.read_raw_fif(fif_path, preload=True, allow_maxshield=True)

def load_ica_files(dataset_name, channel_types):
    all_icas = []
    ica_dir = os.path.join("data", dataset_name, "ica")
    if not os.path.isdir(ica_dir):
        print(f"[WARNING] ICA folder not found: {ica_dir}")
        return []

    for ctype in channel_types:
        ctype_dir = os.path.join(ica_dir, ctype)
        if not os.path.isdir(ctype_dir):
            continue
        for fif_file in os.listdir(ctype_dir):
            if fif_file.endswith("_ica.fif"):
                full_path = os.path.join(ctype_dir, fif_file)
                # parse subj, ses, run from file name convention: subj_ses_run_<ch_type>_ica.fif
                parts = fif_file.split("_")
                if len(parts) >= 4:
                    subj = parts[0]
                    ses  = parts[1]
                    run  = parts[2]
                else:
                    subj, ses, run = ("unknown", "unknown", "unknown")

                trial_id = f"{subj}_{ses}_{run}_{ctype}_ica_{hash(fif_file):x}"
                ica_info = {
                    "trial_id": trial_id,
                    "subj": subj,
                    "ses": ses,
                    "run": run,
                    "ch_type": ctype,
                    "ica_path": full_path,
                    "mode": "ICA"
                }
                all_icas.append(ica_info)
    return all_icas

class session_handler():
    def __init__(self, mode, nTrials, instantfeedback, master_window):
        # Current trial
        self.bad_candidates = []
        self.bad_candidates_shown = []
        self.selected_candidates = []
        self.candidates_shown = []
        self.all_candidate_names = []
        self.topo_window_closed = False
        self.source_window_closed = False
        self.mode = mode
        self.master_window = master_window
        self.instantfeedback = instantfeedback
        # Session Statistics
        self.hits = 0
        self.false_alarms = 0
        self.misses = 0
        self.correct_rejections = 0
        self.missed_channels = []
        self.nTrials = nTrials     

    def init_next_trial(self, trialNR, all_candidate_names, bad_candidates_shown):
        self.all_candidate_names = all_candidate_names
        self.bad_candidates_shown = bad_candidates_shown
        self.trialNR = trialNR
    
    def add_windows(self, topo_window, source_window):
        if not topo_window==None:
            self.topo_window = topo_window
            self.topo_window.canvas.mpl_connect('button_press_event', self.on_candidate_picked)
            self.topo_window.canvas.mpl_connect('close_event', self.on_topo_window_close)
            self.topo_window_closed = False
            
        if not source_window==None:   
            self.source_window = source_window
            callback_ids = list(self.source_window.canvas.callbacks.callbacks.get('pick_event', []))
            for id in callback_ids:
                self.source_window.canvas.mpl_disconnect(id)

            self.source_window.canvas.mpl_connect('button_press_event', self.on_candidate_picked)
            #self.source_window.canvas.mpl_disconnect(self.source_window.mne._callback_ids['pick_event'])
            self.source_window.canvas.mpl_connect('pick_event', self.on_candidate_picked)
            self.source_window.canvas.mpl_connect('close_event', self.on_source_window_close)   
            self.source_window_closed = False

    def on_topo_window_close(self, event):
        self.topo_window_closed = True
        if self.source_window_closed:
            #show end screen
            self.on_all_windows_closed()

    def on_source_window_close(self, event):
        self.source_window_closed = True
        if self.mode == "channels":
            self.on_all_windows_closed()
        if self.topo_window_closed:
            #show end screen
            self.on_all_windows_closed()

    def on_all_windows_closed(self): 
        self.false_alarms = len(self.selected_candidates - set(self.bad_candidates_shown))
        missed_channels = set(self.bad_candidates_shown) - self.selected_candidates
        self.missesmisses = len(missed_channels)
        n_components = config.ica_components
        self.correct_rejections = n_components - len(set(self.bad_candidates_shown) | self.selected_candidates)
        summary_window = TrialEndWindow(
            trial_idx=self.trialNR,
            hits=self.hits,
            false_alarms=self.false_alarms,
            misses=self.misses,
            correct_rejections=self.correct_rejections,
            missed_channels = self.missed_channels
            )
        if summary_window.user_wants_quit:
            self.user_wants_to_quit = True

    # def on_candidate_picked(self, event):
    #     ch_name = ""
    #     #picked a source in the source window (clicked on title)
    #     if isinstance(event, matplotlib.backend_bases.PickEvent):
    #         artist = event.artist         
    #         ch_name = artist.get_text()
    #         if self.mode == "components":
    #         # set text in other window to gray
    #             for figure in self.topo_window.axes:
    #                 if figure.get_label() == ch_name:
    #                     if ch_name in self.selected_candidates:
    #                         figure.set_title(figure.get_label(), color='black')
    #                     else:
    #                          figure.set_title(figure.get_label(), color='gray')
    #                     break

    #     #clicked in topo window (on title) or source window (on timeseries)
    #     elif not event.inaxes:
    #         # Check for title click
    #         for figure in self.topo_window.axes:  # Loop over all figures in the window
    #             #check if label overlaps (with a bit of margin)
    #             if ((event.x >= figure.bbox.min[0]) and 
    #             (event.x <= figure.bbox.max[0]) and 
    #             (event.y >= figure.bbox.min[1]) and 
    #             #somehow the bounding box of the axes doesn't include the title which you just clicked
    #             (event.y <= figure.bbox.max[1] + 20)): 
    #                 ch_name = figure.get_label()
    #                 break

    #         #set text and source in other window to gray
    #         for ind, channel in enumerate(self.source_window.mne.ch_names):
    #             if channel == ch_name:
    #                 if ch_name in self.selected_candidates:
    #                     self.source_window.mne.ch_colors[ind] = [0,0,0]
    #                     self.source_window.canvas.draw()
    #                 else:
    #                     self.source_window.mne.ch_colors[ind] = [0.5,0.5,0.5]
    #                     self.source_window.canvas.draw()
    #                 break
    #     #clicked in source window (on timeseries)

        
    #     elif event.inaxes:
    #         visible_components = self.source_window.mne.params["picks"]
    #         component_axes = self.source_window.axes[:-1] 
    #         #go through timeseries and find the one that was clicked
    #         ax_idx = component_axes.index(event.inaxes)  # Find which subplot was clicked
    #         component_idx = visible_components[ax_idx] 
            
        
    #     #user clicked somewhere unanticipated
    #     else:            
    #         return
    #     if ch_name == "":
    #         return
    #     #evaluate
    #     ch_index = self.all_candidate_names.index(ch_name)
    #     is_correct = ch_index in self.bad_candidates_shown
    #     if ch_name in self.selected_candidates:   
    #         #it's correct to remove an incorrect candidate and vice versa         
    #         is_correct = not is_correct                    
    #         self.selected_candidates.remove(ch_name)
    #         if self.instantfeedback:                    
    #             FeedbackWindow(self.master_window, is_correct)
    #     else:
    #         self.selected_candidates.add(ch_name)
    #         if self.instantfeedback:
    #             FeedbackWindow(self.master_window, is_correct)

    #     if is_correct:
    #         self.hits += 1
    #     else:
    #         self.false_alarms += 1
        
    def on_candidate_picked(self, event):
        ch_name = ""
        # Picked a source in the source window (clicked on title)
        if isinstance(event, matplotlib.backend_bases.PickEvent):
            artist = event.artist         
            ch_name = artist.get_text()
            
        # Clicked in topo window (on title) 
        elif not event.inaxes:
            # Check for title click
            for figure in self.topo_window.axes:
                # Check if label overlaps (with a bit of margin)
                if ((event.x >= figure.bbox.min[0]) and 
                    (event.x <= figure.bbox.max[0]) and 
                    (event.y >= figure.bbox.min[1]) and 
                    (event.y <= figure.bbox.max[1] + 20)): 
                    ch_name = figure.get_label()
                    break

        # Clicked in source window (on timeseries)
        elif event.inaxes:
            traces = self.source_window.mne.traces  # List of Line2D objects
            
            # Find which trace was clicked using MNE's internal logic
            for line in traces:
                if line.contains(event)[0]:  # Check if click is on this line
                    # Map line to component index
                    component_idx = self.source_window.mne.traces.index(line)
                    ch_name = self.source_window.mne.ch_names[component_idx]
                    break
        else:            
            return        
        if ch_name == "":
            return
        
        # Evaluate selection correctness
        ch_index = self.all_candidate_names.index(ch_name)
        is_correct = ch_index in self.bad_candidates_shown
        if ch_name in self.selected_candidates:   
            is_correct = not is_correct                    
            self.selected_candidates.remove(ch_name)
            if self.instantfeedback:                    
                FeedbackWindow(self.master_window, is_correct)
        else:
            self.selected_candidates.append(ch_name)
            if self.instantfeedback:
                FeedbackWindow(self.master_window, is_correct)

        # Update source window colors
        for ind, channel in enumerate(self.source_window.mne.ch_names):
            color = [0.5, 0.5, 0.5] if channel in self.selected_candidates else [0, 0, 0]
            self.source_window.mne.ch_colors[ind] = color
            self.source_window.mne.traces[ind].set_color(color)

        # to prevent weird mne picking bug always set all label colors to black
        for label in self.source_window.axes[0].get_yticklabels():                
            label.set_color([0.0, 0.0, 0.0, 1.0])

        self.source_window.canvas.draw_idle()        

        # Update topo window titles
        for figure in self.topo_window.axes:
            label = figure.get_label()
            color = 'gray' if label in self.selected_candidates else 'black'
            figure.set_title(label, color=color)
        self.topo_window.canvas.draw()

        # Update performance metrics
        if is_correct:
            self.hits += 1
        else:
            self.false_alarms += 1

