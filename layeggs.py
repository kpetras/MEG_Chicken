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


def read_meeg_bad_channels(bad_dict, data_dir):
    """
    1) Iterate over MEEG files in data_dir
    2) For each file, read raw.info['bads'], distribute them to 'badC_EEG' or 'badC_MEG'.
    """
    data_files = [f for f in os.listdir(data_dir) if not f.startswith('.')]
    if not data_files:
        print(f"[MEEG] No files found in {data_dir}. Skipping MEEG mode.")
        return

    for data_file in data_files:
        file_path = os.path.join(data_dir, data_file)
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

def pick_ica_components(file_path, bad_dict, n_components=config.ica_components, method=config.ica_method, random_state = config.ica_seed):
    """
    1) Parse subj, ses, run from file name
    2) read_raw asssmed preprocessed
    3) Detect which channel types (EEG, Mag, Grad) exist
    4) For each present channel type, fit ICA, let user select comps, store in 'ICA_remove_inds'
    """
    filename = os.path.basename(file_path)
    try:
        subj, ses, run = filename.split('_')[:3]
    except ValueError:
        print(f"[WARN] {filename} not in 'subj_ses_run' format. Skipping.")
        return

    print(f"\n=== Processing: subj={subj}, ses={ses}, run={run}, file={filename} ===")

    # Read raw
    try:
        raw = mne.io.read_raw(file_path, preload=True, allow_maxshield=True)
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
        fig = ica.plot_components(title=title_str, show=False)
        plt.show(block=True)

        excluded_comps = list(ica.exclude)
        print(f"[ICA] Excluded comps for {ch_type}: {excluded_comps}")

        # Store them in the dict
        # bad_dict["ICA_remove_inds"][subj][ses][run][ch_type] = [excluded comps]
        ica_inds_dict = bad_dict["ICA_remove_inds"]
        ensure_hierarchy(ica_inds_dict, subj, ses, run, if_ica = True)
        ica_inds_dict[subj][ses][run][ch_type] = excluded_comps

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

    bad_dict = {
        "badC_EEG": {},
        "badC_MEG": {},
        "ICA_remove_inds": {}
    }

    # If MEEG
    if "meeg" in cmds:
        print("[INFO] MEEG mode: scanning raw files for bad channels.")
        read_meeg_bad_channels(bad_dict, data_dir=config.nest_dir)

    # If ICA
    if "ica" in cmds:
        print("[INFO] ICA mode: opening raw files for picking components.")
        pick_ica_components(bad_dict, ica_dir=config.nest_dir)

    # If nothing, do nothing
    if not cmds:
        print("No commands specified. Usage example: `python script.py MEEG ICA`. Exiting.")
        return

    answer_dir = config.answer_dir
    os.makedirs(answer_dir, exist_ok=True)

    output_json_path = os.path.join(answer_dir, args.output)
    output_json_path = get_unique_filename(output_json_path)

    with open(output_json_path, 'w', encoding='utf-8') as jf:
        json.dump(bad_dict, jf, indent=2, ensure_ascii=False)

    print(f"[DONE] Output JSON saved to: {output_json_path}")


if __name__ == "__main__":
    main()
