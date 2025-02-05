from scipy.stats import norm
import os
import random
from tkinter import messagebox
import json
import numpy as np
import mne
import sqlite3
import pickle
# -----------------------------------------
#           Everything Calculation
# -----------------------------------------
def compute_dprime(hits, false_alarms, misses, correct_rejections):
    """
    Compute d-prime based on hits/misses/false alarms/correct rejections.
    
    D-prime = Z(HR) - Z(FAR)
    Where:
    HR = hits / (hits + misses)
    FAR = false_alarms / (false_alarms + correct_rejections)
    """
    total_signal = hits + misses # Pos
    total_noise  = false_alarms + correct_rejections # Negs

    if hits == 0: hits = 1
    if false_alarms == 0: false_alarms = 1
    if hits == total_signal: hits = hits - 1
    if false_alarms == total_noise: false_alarms = false_alarms - 1

    if total_signal == 0 or total_noise == 0:
        return 0.0

  
    pHit = hits / total_signal 
    pFA  = false_alarms / total_noise 

    # Convert to Z scores, no error checking
    zHit = norm.ppf(pHit)
    zFA = norm.ppf(pFA)

    dprime = zHit - zFA

    # crit = (zHit + zFA) / -2
    # crit_prime = crit / dprime    
    return dprime
# -----------------------------------------
#           Everything Dataset
# -----------------------------------------
def scan_directories(scan_answers=False):
    """
    Scans stuffs
    """
    if scan_answers:
        data_root = os.path.join("data", "answer")
        try:
            all_items = os.listdir(data_root)
        except FileNotFoundError:
            messagebox.showerror("Error", f"Answer directory '{data_root}' not found.")
            return []
        return [item for item in all_items if item.endswith(".json")]
    
    else:
        data_root = "data"
        excluded_dirs = {"raw", "answer", "session_data", "results"}
        try:
            all_items = os.listdir(data_root)
        except FileNotFoundError:
            messagebox.showerror("Error", f"Data folder '{data_root}' not found.")
            return []
        
        return [item for item in all_items if os.path.isdir(os.path.join(data_root, item)) and item not in excluded_dirs]

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

# -----------------------------------------
#           Everything Trials
# -----------------------------------------
def pick_random_trials(trials_list, n_trial):
    random.shuffle(trials_list)
    if len(trials_list) <= n_trial:
        return trials_list
    return random.sample(trials_list, n_trial)
