# config.py
import os
# Directories
data_dir = 'data'
raw_dir = os.path.join('data', 'raw')
ica_dir = os.path.join('data', 'ica')

res_dir = os.path.join('data', 'results')
preproc_dir = os.path.join('data', 'preproc')
session_dir = os.path.join('data', 'session_data')
answer_dir = os.path.join('data', 'answer')
exclude_dirs = [os.path.basename(raw_dir), 
                os.path.basename(res_dir), 
                os.path.basename(session_dir), 
                os.path.basename(answer_dir)]

# Experiment setups
n_trials_per_session = 15

# ICA settings
ica_components = 50 # The number of ICA components should be less than 50
ica_method = 'fastica'
ica_seed = 42

# Preprocessing settings
l_freq = 0.1  # High-pass filter cutoff (default=0.1 Hz)
h_freq = 80.0  # Low-pass filter cutoff (default=80 Hz)
notch_freq = 50.0  # Base notch filter frequency (default=50 Hz)

# Trial settings
total_channels = 15  # Number of channels in each snippet (default=15)
max_bad_ch = 3  # Max bad channels forced in snippet (default=3)
min_bad_ch = 1  # Min bad channels forced in snippet (default=1)