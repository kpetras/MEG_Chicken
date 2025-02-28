# initializeChicken.py
"""
This file does the followings:
1.  Check if the current environment has all necessary packages according to
    requirements.txt; if not, raise a warning.
2.  Create all necessary directories.
3.  Download the MNE example FIF file for instructional purposes.
"""
import os
import sys
try:
    from importlib.metadata import distributions # for python 3.8+
except ImportError:
    from importlib_metadata import distributions
import config
import shutil

def check_requirements(requirements_file="requirements.txt"):
    """
    Check if each package specified in requirements.txt is installed.
    Only a basic check is performed: if the package key (name) is missing in the working set,
    a warning is printed.
    """
    if not os.path.exists(requirements_file):
        print(f"[WARNING] {requirements_file} does not exist.")
        return
    with open(requirements_file, "r") as f:
        required = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    installed = {dist.metadata["Name"].lower() for dist in distributions()}
    missing = []
    for req in required:
        pkg_name = req.split("==")[0].strip().lower()
        if pkg_name not in installed:
            print(f"[WARNING] Package '{pkg_name}' is not installed. Please install it.")
            missing.append(pkg_name)
    if missing:
        print(f"[ERROR] The following required packages are missing: {', '.join(missing)}. Exiting...")
        sys.exit(1)

def main():
    # Check if the current environment has all necesarry packages before running anything
    check_requirements()
    import mne
    # Create necessary directories.
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print("[INFO] Root directory created")
    subDirs = [config.raw_dir, config.ica_dir, os.path.join(config.ica_dir, 'eeg'),
            os.path.join(config.ica_dir, 'mag'), os.path.join(config.ica_dir, 'grad'),
            config.res_dir, config.session_dir, config.answer_dir, config.preproc_dir]
    for subDir in subDirs:
        if not os.path.exists(subDir):
            os.makedirs(subDir)
            print(f"[INFO] {subDir} sub-directory created")        
    # Download the MNE sample dataset
    sample_filename = "sample_audvis_raw.fif"
    destination_file = os.path.join(config.raw_dir, sample_filename)
    
    # If the file already exists in the raw directory, skip download.
    if os.path.exists(destination_file):
        print(f"[INFO] {sample_filename} already exists in {config.raw_dir}.")
        return
    # Else download
    print("[INFO] Downloading MNE example dataset...")
    print("[INFO] MNE only allows downloading the entire dataset at once...")
    sample_dataset_path = mne.datasets.sample.data_path(verbose=True)
    sample_file_path = os.path.join(sample_dataset_path, "MEG", "sample", sample_filename)
    if not os.path.exists(sample_file_path):
        print(f"[ERROR] {sample_file_path} does not exist in the downloaded dataset.")
        return
    shutil.copy2(sample_file_path, destination_file)
    print(f"[INFO] Copied {sample_filename} to {destination_file}")
    if os.path.exists(sample_dataset_path):
        shutil.rmtree(sample_dataset_path)
        print(f"[INFO] Removed downloaded dataset directory: {sample_dataset_path}")
    print("[INFO] Chicken initialization complete")
    print("[INFO] You can now run prepChicken.py to start preprocessing")
    print("[INFO] Or you can first add your own data to the 'data/raw' directory")
if __name__ == "__main__":
    main()

