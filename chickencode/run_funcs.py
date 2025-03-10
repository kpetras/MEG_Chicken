
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
        self.selected_candidates = set()
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

    def on_candidate_picked(self, event):

        #picked a source in the source window
        if isinstance(event, matplotlib.backend_bases.PickEvent):
            artist = event.artist         
            ch_name = artist.get_text()
            if self.mode == "channels":
                print(ch_name)
            elif self.mode == "sources":
                print(ch_name)
            else:
                print("Error: Mode not recognized")
            
        #is not a click on topo plot/ in source window 
        elif not event.inaxes:
            # Check for title click
            for figure in self.topo_window.axes:  # Loop over all figures in the window
                #check if label overlaps (with a bit of margin)
                if ((event.x >= figure.bbox.min[0]) and 
                (event.x <= figure.bbox.max[0]) and 
                (event.y >= figure.bbox.min[1]) and 
                #somehow the bounding box of the axes doesn't include the title which you just clicked
                (event.y <= figure.bbox.max[1] + 20)): 
                    ch_name = figure.get_label()
                    break
        #user clicked somewhere unanticipated
        else:            
            return
        #evaluate
        
        ch_index = self.all_candidate_names.index(ch_name)
        is_correct = ch_index in self.bad_candidates_shown
        if ch_name in self.selected_candidates:   
            #it's correct to remove an incorrect candidate and vice versa         
            is_correct = not is_correct                    
            self.selected_candidates.remove(ch_name)
            if self.instantfeedback:                    
                FeedbackWindow(self.master_window, is_correct)
        else:
            self.selected_candidates.add(ch_name)
            if self.instantfeedback:
                FeedbackWindow(self.master_window, is_correct)

        if is_correct:
            self.hits += 1
        else:
            self.false_alarms += 1
