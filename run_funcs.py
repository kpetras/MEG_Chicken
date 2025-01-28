from scipy.stats import norm
import os
import random
from tkinter import messagebox
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
    # pHit = hits / total_signal
    # pFA  = false_alarms / total_noise

    # Convert to Z scores, no error checking
    zHit = norm.ppf(pHit)
    zFA = norm.ppf(pFA)

    dprime = zHit - zFA

    # crit = (zHit + zFA) / -2
    # crit_prime = crit / dprime    
    return dprime

def collect_files(data_path, channel_types, file_extension, mode):
    all_files = []
    for ch_type in channel_types:
        ch_dir = os.path.join(data_path, ch_type)
        if os.path.isdir(ch_dir):
            files_in_ch_dir = [
                f for f in os.listdir(ch_dir) if f.endswith(file_extension)
            ]
            all_files.extend([(ch_type, file) for file in files_in_ch_dir])
        else:
            print(f"Warning: {ch_dir} not found or is not a directory.")
    
    if len(all_files) == 0:
        print(f"No {mode} files found for the specified channel types.")
        return None
    
    return all_files

def process_trial_files(all_files, n_trials, mode, data_path):

    trials_list = []
    chosen_files = random.sample(all_files, min(n_trials, len(all_files)))

    for trial_idx, (ch_type, trial_file) in enumerate(chosen_files, start=1):

        full_path = os.path.join(data_path, ch_type, trial_file) 
        
        trials_list.append({
            "Trial": trial_idx,
            "trial_file": trial_file,
            "ch_type": ch_type,
            "trial_path": full_path,
            "mode": mode
        })
    
    return trials_list

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
