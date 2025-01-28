# config.py
import os
# Directories
raw_dir = os.path.join('data', 'raw')
# trials_dir = os.path.join('data', 'trials')
# ica_dir = os.path.join('data', 'ica')
# preprocessed_save_path = os.path.join('data', 'preprocessed')
res_dir = os.path.join('data', 'results')
# sample_dir = os.path.join('data', 'sample')
session_dir = os.path.join('data', 'session_data')
answer_dir = os.path.join('data', 'answer')
nest_dir = os.path.join('data', 'nest') # Where the chicken lay eggs. HA! Get it?

# Experiment setups
n_trials_per_session = 5

# ICA settings
ica_components = 50 
ica_method = 'fastica'
ica_seed = 42

# Preprocessing settings
l_freq = 0.1  # High-pass filter cutoff (default=0.1 Hz)
h_freq = 80.0  # Low-pass filter cutoff (default=80 Hz)
notch_freq = 50.0  # Base notch filter frequency (default=50 Hz)

# Trial settings
n_versions = 3  # Number of trial-version repeats (default=3)
trials_per_file = 5  # Trials per version per channel_type (default=5)
total_channels = 15  # Number of channels in each snippet (default=15)
max_bad_ch = 3  # Max bad channels forced in snippet (default=3)
min_bad_ch = 1  # Min bad channels forced in snippet (default=1)