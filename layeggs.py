# layeggs.py
import os
import mne
import argparse
import json
import matplotlib
import matplotlib.pyplot as plt

import config  # your config with nest_dir, ica_dir, etc.

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

def ensure_hierarchy(storage_dict, subj, ses, run, if_ica=False):
    """
    Helper to ensure the nested keys exist in the provided `storage_dict[subj][ses][run]`.
    """
    if subj not in storage_dict:
        storage_dict[subj] = {}
    if ses not in storage_dict[subj]:
        storage_dict[subj][ses] = {}
    if run not in storage_dict[subj][ses]:
        if if_ica:
            # For ICA dictionary: run will be a dictionary to store channel types
            storage_dict[subj][ses][run] = {}
        else:
            # For MEEG dictionary: run will be a list to store bad channels
            storage_dict[subj][ses][run] = []

    return storage_dict

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

def read_meeg_bad_channels(bad_dict, data_dir):
    """
    1) Iterate over MEEG files in data_dir
    2) For each file, read raw.info['bads'], distribute them to 'badC_EEG' or 'badC_MEG'.
    """
    data_files = [f for f in os.listdir(data_dir) if not f.startswith('.')]
    print("data_files",data_files)
    if not data_files:
        print(f"[MEEG] No files found in {data_dir}. Skipping MEEG mode.")
        return bad_dict

    for data_file in data_files:
        file_path = os.path.join(data_dir, data_file)
        print("file_path", file_path)
        # Expect subj_ses_run in the filename
        try:
            subj, ses, run = data_file.split('_')[:3]
        except ValueError:
            print(f"[MEEG] File name {data_file} not in expected subj_ses_run format. Skipping.")
            continue

        print(f"[MEEG] Reading file: {file_path}")
        try:
            raw = mne.io.read_raw(file_path, preload=False, allow_maxshield=True)
        except Exception as e:
            print(f"[MEEG] Failed to read {file_path}: {e}")
            continue

        all_bads = raw.info['bads']
        print("raw.info['bads']", all_bads)
        eeg_bads = []
        meg_bads = []
        for ch_name in all_bads:
            if ch_name.startswith("EEG"):
                eeg_bads.append(ch_name)
            elif ch_name.startswith("MEG"):
                meg_bads.append(ch_name)

        if eeg_bads:
            badE = bad_dict["badC_EEG"]
            badE = ensure_hierarchy(badE, subj, ses, run, if_ica = False)
            bad_dict["badC_EEG"][subj][ses][run].extend(eeg_bads)

        if meg_bads:
            badM = bad_dict["badC_MEG"]
            badM = ensure_hierarchy(badM, subj, ses, run, if_ica =False)
            bad_dict["badC_MEG"][subj][ses][run].extend(meg_bads)

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

def pick_ica_components(bad_dict, data_dir, n_components=config.ica_components, method=config.ica_method, random_state = config.ica_seed):
    """
    1) Parse subj, ses, run from file name
    2) Read raw (assumed preprocessed)
    3) Detect which channel types (EEG, Mag, Grad) exist
    4) For each present channel type, fit ICA, let user select comps, store in 'ICA_remove_inds'
    """
    data_files = [f for f in os.listdir(data_dir) if not f.startswith('.')]
    if not data_files:
        print(f"[ICA] No files found in {data_dir}. Skipping ICA mode.")
        return
    for data_file in data_files:
        file_path = os.path.join(data_dir, data_file)
        filename = os.path.basename(file_path)
        try:
            subj, ses, run = filename.split('_')[:3]
        except ValueError:
            print(f"[WARN] {filename} not in 'subj_ses_run' format. Skipping.")
            return

        print(f"\n=== Processing: subj={subj}, ses={ses}, run={run}, file={filename} ===")

        # Read raw
        try:
            raw = mne.io.read_raw(file_path, preload=False, allow_maxshield=True)
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")
            return

        # Detect channel types
        present_types = detect_channel_types(raw)
        if not present_types:
            print(f"No EEG/MAG/GRAD found in {filename}. Skipping ICA.")
            return

        # For each channel type, do a separate ICA
        for ch_type in present_types:
            # Build picks
            if ch_type == 'eeg':
                picks = mne.pick_types(raw.info, eeg=True, meg=False)
            elif ch_type == 'mag':
                picks = mne.pick_types(raw.info, meg='mag', eeg=False)
            elif ch_type == 'grad':
                picks = mne.pick_types(raw.info, meg='grad', eeg=False)

            print(f"[ICA] Fitting {ch_type} ICA for {filename} ... (n_components={n_components}, method={method})")
            ica = mne.preprocessing.ICA(n_components=n_components, method=method, random_state=random_state)
            ica.fit(raw, picks=picks)

            title_str = f"{subj}_{ses}_{run}_{ch_type} - close window to finalize"
            ica.plot_components(title=title_str, 
                                nrows = 5,
                                ncols = 10,
                                show=False)
            plt.show(block=True)

            excluded_comps = list(ica.exclude)
            print(f"[ICA] Excluded comps for {ch_type}: {excluded_comps}")

            # Store them in the dict
            # bad_dict["ICA_remove_inds"][subj][ses][run][ch_type] = [excluded comps]
            ica_inds_dict = bad_dict["ICA_remove_inds"]
            ensure_hierarchy(ica_inds_dict, subj, ses, run, if_ica = True)
            bad_dict["ICA_remove_inds"][subj][ses][run][ch_type] = excluded_comps
    return bad_dict

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

    bad_dict_new = {
        "badC_EEG": {},
        "badC_MEG": {},
        "ICA_remove_inds": {}
    }

    # If MEEG
    if "meeg" in cmds:
        print("[INFO] MEEG mode: scanning raw files for bad channels.")
        bad_dict_new = read_meeg_bad_channels(bad_dict_new, data_dir=config.nest_dir)
        print(bad_dict_new["badC_EEG"])

    # If ICA
    if "ica" in cmds:
        print("[INFO] ICA mode: opening raw files for picking components.")
        bad_dict_new = pick_ica_components(bad_dict_new, data_dir=config.nest_dir)

    # If nothing, do nothing
    if not cmds:
        print("No commands specified. Usage example: `python script.py MEEG ICA`. Exiting.")
        return

    answer_dir = config.answer_dir
    os.makedirs(answer_dir, exist_ok=True)

    output_json_path = os.path.join(answer_dir, args.output)
    # If the file ALREADY exists, ask user if they want to build on it (merge)
    if os.path.exists(output_json_path):
        print(f"File already exists: {output_json_path}")
        user_resp = input("Do you want to build on that existing file? (y/n): ").strip().lower()
        if user_resp in ("y", "yes"):
            # Read and Merge
            with open(output_json_path, 'r', encoding='utf-8') as jf:
                file_content = jf.read().strip()
                if not file_content:  # Check if file is empty
                    print("[WARNING] Existing JSON file is empty. Using an empty dictionary.")
                    return
                else:
                    bad_dict_old = json.loads(file_content) 
            merged_dict = merge_bad_dicts(bad_dict_old, bad_dict_new)

            # Overwrite
            with open(output_json_path, 'w', encoding='utf-8') as jf:
                json.dump(merged_dict, jf, indent=2, ensure_ascii=False)
            print(f"[DONE] Merged updates and overwrote {output_json_path}")
            return
        else:
            # If user chooses NO, pick a unique new filename
            print("User chose not to build on existing. Creating a new file name ...")
            output_json_path = get_unique_filename(output_json_path)

    with open(output_json_path, 'w', encoding='utf-8') as jf:
        json.dump(bad_dict_new, jf, indent=2, ensure_ascii=False)

    print(f"[DONE] Output JSON saved to: {output_json_path}")


if __name__ == "__main__":
    main()
