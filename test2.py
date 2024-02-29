# %%
# Import packages 
import numpy as np
from psychopy import visual, core
import mne

# Load EEG data
path = '/Users/coline/Desktop/Internship/03TPZ5_session2_run01.fif'
raw = mne.io.read_raw_fif(path, preload=True, allow_maxshield=True)

# Downsample the data
raw_resampled = raw.copy().resample(250, npad="auto")

# Add channels to the list of "bad datas"
channels_to_mark_as_bad = ['MEG0332','MEG1022','MEG1143','MEG1242','MEG1333','MEG1433','MEG2013','MEG2023','MEG2413','MEG2623','MEG0121','MEG1931']
raw_resampled.info['bads'].extend(channels_to_mark_as_bad)

# Define channels
all_channels = raw.info['ch_names']
bad_channels = raw.info['bads']
good_channels = [ch for ch in all_channels if ch not in bad_channels]

# %%
# Select a random channel from all channels
selected_channel = np.random.choice(all_channels)

# Créer une fenêtre PsychoPy
win = visual.Window([800, 600], monitor="testMonitor", units="deg")

# Créer un tableau de valeurs d'EEG simulées pour le canal sélectionné
eeg_data = raw_resampled.copy().pick_channels([selected_channel])[0][0]

# Définir les paramètres de l'affichage EEG
num_samples = len(eeg_data)
x_values = np.linspace(-10, 10, num_samples)  # Valeurs x pour le tracé EEG
y_values = eeg_data  # Valeurs y (données EEG)

# Créer un objet de ligne PsychoPy pour afficher l'EEG
eeg_line = visual.Line(
    win=win,
    start=(-10, 0),
    end=(10, 0),
    lineColor='white',
    lineWidth=2
)

# Afficher l'EEG en boucle
for i in range(num_samples):
    eeg_line.setVertices(((-10, y_values[i]), (10, y_values[i])))
    eeg_line.draw()
    win.flip()

    # Attendre un court instant avant de passer à l'échantillon suivant
    core.wait(0.01)

# Fermer la fenêtre PsychoPy à la fin
win.close()

