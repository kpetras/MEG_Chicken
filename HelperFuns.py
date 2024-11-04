# HelperFuns.py
import random

def select_and_shuffle_channels(raw, bad_channels, channel_type, total_channels=15, max_bad_channels=3, min_bad_channels = 1):
    """
    Selects and shuffles channels of a specific type, including a random selection of bad ones.

    Args:
        raw (mne.io.Raw): Raw data.
        bad_channels (list): List of known bad channels.
        channel_type (str): Type of channels to select ('EEG', 'Mag', 'Grad').
        total_channels (int): Total number of channels to select.
        max_bad_channels (int): Maximum number of bad channels to include.

    Returns:
        tuple: (selected_channels, bad_chans_in_display)
    """
    all_channels = raw.ch_names

    # Filter channels by type
    if channel_type == 'EEG':
        type_channels = [ch for ch in all_channels if ch.startswith('EEG')]
    elif channel_type == 'Mag':
        type_channels = [ch for ch in all_channels if ch.startswith('MEG') and ch.endswith('1')]
    elif channel_type == 'Grad':
        type_channels = [ch for ch in all_channels if ch.startswith('MEG') and ch.endswith(('2', '3'))]
    else:
        raise ValueError(f"Invalid channel type: {channel_type}")

    # Separate good and bad channels
    good_channels = [ch for ch in type_channels if ch not in bad_channels]
    bad_channels_in_type = [ch for ch in bad_channels if ch in type_channels]

    # Randomly select bad channels
    num_bad = min(random.randint(min_bad_channels, max_bad_channels), len(bad_channels_in_type))
    selected_bad_channels = random.sample(bad_channels_in_type, num_bad)

    # Randomly select good channels
    num_good = total_channels - num_bad
    selected_good_channels = random.sample(good_channels, min(num_good, len(good_channels)))

    # Combine and shuffle
    selected_channels = selected_good_channels + selected_bad_channels
    random.shuffle(selected_channels)

    return selected_channels, selected_bad_channels