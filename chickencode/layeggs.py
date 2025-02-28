# layeggs.py
import os
import mne
import argparse
import json
import matplotlib
import matplotlib.pyplot as plt
import config
import copy

# ============ MNE Matplotlib settings ============
mne.viz.set_browser_backend('matplotlib')
matplotlib.use('tkagg')


def get_unique_filename(base_path):
    """
    Making sure that the file name is unique instead of overwriting the existing ones
    """
    if not os.path.exists(base_path):
        return base_path

    dir_name, file_name = os.path.split(base_path)
    basename, ext = os.path.splitext(file_name)

    i = 1
    while True:
        new_name = f"{basename}_{i}{ext}"
        candidate_path = os.path.join(dir_name, new_name)
        if not os.path.exists(candidate_path):
            return candidate_path
        i += 1

def merge_bad_dicts(old_dict, new_dict):
    """
    If the user want to build on an existing answer dict, we merge them
    ICA: storage_dict[subj][ses][run][ch_type] = []
    MEEG: storage_dict[subj][ses][run] = []
    """
    expected_keys = {"badC_EEG", "badC_MEG", "ICA_remove_inds"}
    # Check if old_dict has valid structure
    if not isinstance(old_dict, dict):
        print("[WARNING] Your json file does not have the correct structure. Merge skipped.")
        return old_dict
    
    for key in expected_keys:
        if key in old_dict and not isinstance(old_dict[key], dict):
            print(f"[WARNING] Your json file's key {key} does not follow the expected structure. Merge skipped.")
            return old_dict
        
     # Merge top-level keys: "badC_EEG", "badC_MEG", "ICA_remove_inds"
    for key in new_dict:
        if key not in old_dict:
            old_dict[key] = new_dict[key]
            continue
        if key in ("badC_EEG", "badC_MEG"):
            # structure: old_dict[key][subj][ses][run] => list
            for subj, subj_data in new_dict[key].items():
                if subj not in old_dict[key]:
                    old_dict[key][subj] = subj_data
                    continue
                for ses, ses_data in subj_data.items():
                    if ses not in old_dict[key][subj]:
                        old_dict[key][subj][ses] = ses_data
                        continue
                    for run, run_bads in ses_data.items():
                        if run not in old_dict[key][subj][ses]:
                            old_dict[key][subj][ses][run] = run_bads
                        else:
                            old_dict[key][subj][ses][run].extend(run_bads)
        elif key == "ICA_remove_inds":
            # structure: old_dict["ICA_remove_inds"][subj][ses][run][ch_type] => list
            for subj, subj_data in new_dict[key].items():
                if subj not in old_dict[key]:
                    old_dict[key][subj] = subj_data
                    continue
                for ses, ses_data in subj_data.items():
                    if ses not in old_dict[key][subj]:
                        old_dict[key][subj][ses] = ses_data
                        continue
                    for run, run_dict in ses_data.items():
                        if run not in old_dict[key][subj][ses]:
                            old_dict[key][subj][ses][run] = run_dict
                            continue
                        # now run_dict => { ch_type => [excluded comps] }
                        for ch_type, comps_list in run_dict.items():
                            if ch_type not in old_dict[key][subj][ses][run]:
                                old_dict[key][subj][ses][run][ch_type] = comps_list
                            else:
                                old_dict[key][subj][ses][run][ch_type].extend(comps_list)

    return old_dict                            

def read_meeg_bad_channels(bad_dict, data_file):
    """
    1) Iterate over MEEG files in data_dir
    2) For each file, read raw.info['bads'], distribute them to 'badC_EEG' or 'badC_MEG'.   """

    file_path = os.path.join(config.raw_dir, data_file)
    try:
        raw = mne.io.read_raw(file_path, preload=False, allow_maxshield=True)
    except Exception as e:
        print(f"[MEEG] Failed to read {file_path}: {e}")
        

    all_bads = raw.info['bads']
    print("raw.info['bads']", all_bads)
    eeg_bads = []
    meg_bads = []
    for ch_name in all_bads:
        if ch_name.startswith("EEG"):
            eeg_bads.append(ch_name)
        elif ch_name.startswith("MEG"):
            meg_bads.append(ch_name)

    # if eeg_bads: create the structure even if there's no bads
    bad_dict["badC_EEG"].extend(eeg_bads)

    # if meg_bads: create the structure even if there's no bads
    bad_dict["badC_MEG"].extend(meg_bads)

    return bad_dict

def detect_channel_types(raw):
    """
    Return a list of the channel types present among ['eeg', 'mag', 'grad'].
    """
    present_types = []
    picks_eeg = mne.pick_types(raw.info, meg=False, eeg=True)
    if len(picks_eeg) > 0:
        present_types.append('eeg')

    picks_mag = mne.pick_types(raw.info, meg='mag')
    if len(picks_mag) > 0:
        present_types.append('mag')

    picks_grad = mne.pick_types(raw.info, meg='grad')
    if len(picks_grad) > 0:
        present_types.append('grad')

    return present_types

def pick_ica_components(bad_dict, data_file, n_components=config.ica_components, method=config.ica_method, random_state = config.ica_seed):
    """
    1) Parse subj, ses, run from file name
    2) Read raw (assumed preprocessed)
    3) Detect which channel types (EEG, Mag, Grad) exist
    4) For each present channel type, fit ICA, let user select comps, store in 'ICA_remove_inds'
    """
    filename = os.path.join(config.raw_dir, data_file)

    print(f"\n=== Processing: {data_file}  ===")

    # Read raw
    try:
        raw = mne.io.read_raw(filename, preload=False, allow_maxshield=True)
    except Exception as e:
        print(f"Failed to read {filename}: {e}")
        return

    # Detect channel types
    present_types = detect_channel_types(raw)
    if not present_types:
        print(f"No EEG/MAG/GRAD found in {filename}. Skipping ICA.")
        return

    # For each channel type, do a separate ICA
    for ch_type in present_types:
        ica = mne.preprocessing.read_ica(os.path.join(config.ica_dir, ch_type, data_file[:-4] + '_ica.fif'))
        #make sure that second window also captures excluded components
        ica2 = copy.deepcopy(ica)
        title_str = f"{filename} - close window to finalize"
        ica.plot_sources(title=title_str, 
                            inst = raw,
                            show = False)
        plt.show(block=False)
        title_str = f"{filename} - close window to finalize"
        ica2.plot_components(title=title_str, 
                            inst = raw,
                            nrows = 5,
                            ncols = 10,
                            show=False)
        plt.show(block=True)

        excluded_comps1 = list(ica.exclude)
        excluded_comps2 = list(ica2.exclude)
        excluded_comps = list(set(excluded_comps1 + excluded_comps2))
        print(f"[ICA] Excluded comps for {ch_type}: {excluded_comps}")

        # Store them in the dict
        bad_dict["ICA_remove_inds_" +  ch_type] = excluded_comps

def makeAns(cmds,answer_file, data_file, pick_bad_channels=True, pick_bad_components=True):

    bad_dict_new = {
        "badC_EEG": [],
        "badC_MEG": [],
        "ICA_remove_inds_eeg": [],
        "ICA_remove_inds_mag": [],
        "ICA_remove_inds_grad": [],
    }

    # If MEEG
    if pick_bad_channels:
        print("[INFO] Currently does the wrong thing, Needs to be done.")
        bad_dict_new = read_meeg_bad_channels(bad_dict_new, data_file=data_file)
    else:
        bad_dict_new = read_meeg_bad_channels(bad_dict_new, data_file=data_file)
        print(bad_dict_new["badC_EEG"])

    # If ICA
    if pick_bad_components:
        print("[INFO] ICA mode: opening raw files for picking components.")
        pick_ica_components(bad_dict_new, data_file=data_file)

    # If nothing, do nothing
    if not cmds:
        print("No commands specified. Usage example: `python script.py MEEG ICA`. Exiting.")
        return

    # Read existing JSON file (that might be empty) and add to it
    with open(answer_file, 'r', encoding='utf-8') as jf:
        file_content = jf.read().strip()
        if not file_content:  # Check if file is empty
            print("[WARNING] Existing JSON file is empty. Using an empty dictionary.")
            return
        else:
            bad_dict_old = json.loads(file_content) 
    merged_dict = merge_bad_dicts(bad_dict_old, bad_dict_new)
    
    return merged_dict



def main():
    parser = argparse.ArgumentParser(
        description="Generate or update a JSON of bad channels and/or ICA components."
    )
    parser.add_argument(
        "commands",
        nargs="*",
        help="Which modes to run: MEEG, ICA. e.g. `python script.py MEEG ICA` does both."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="answer_new.json",
        help="Name of the output JSON (default=answer_new(_num).json)."
    )

    args = parser.parse_args()
    cmds = [c.lower() for c in args.commands]

    makeAns(cmds)

if __name__ == "__main__":
    main()
