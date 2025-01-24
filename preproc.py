# preproc.py
# This script is just for the parser check preproc_funcs.py for specification
import os
import argparse
import config
from preproc_funcs import (
    preprocess_and_make_trials
)

def main():
    parser = argparse.ArgumentParser(
        description="Script to preprocess MEEG data, optionally run ICA, and/or make trial snippets."
    )

    # Positional arguments: commands (case-insensitive)
    # e.g. python preproc.py MEEG ICA
    parser.add_argument(
        "commands", 
        nargs="*", 
        help=(
            "Commands: MEEG, MEG, EEG, MAG, GRAD, ICA, TRIAL(S), etc. (case-insensitive). "
            "MEEG/MEG/EEG/MAG/GRAD define which channels to process, "
            "'ICA' triggers ICA, 'TRIAL' triggers trial generation, "
        )
    )

    # Common optional arguments
    parser.add_argument("--l-freq", type=float, default=config.l_freq, help="High-pass filter cutoff (default=0.1 Hz).")
    parser.add_argument("--h-freq", type=float, default=config.h_freq, help="Low-pass filter cutoff (default=80 Hz).")
    parser.add_argument("--notch-freq", type=float, default=config.notch_freq, help="Base notch filter frequency (default=50 Hz).")

    parser.add_argument("--n-versions", type=int, default=config.n_versions, help="Number of trial-version repeats (default=3).")
    parser.add_argument("--trials-per-file", type=int, default=config.trials_per_file, help="Trials per version per channel_type (default=5).")
    parser.add_argument("--total-channels", type=int, default=config.total_channels, help="Number of channels in each snippet (default=15).")
    parser.add_argument("--max-bad-ch", type=int, default=config.max_bad_ch, help="Max bad channels forced in snippet (default=3).")
    parser.add_argument("--min-bad-ch", type=int, default=config.min_bad_ch, help="Min bad channels forced in snippet (default=1).")

    # ICA-related optional arguments
    parser.add_argument("--n-components", type=int, default=50, help="Number of ICA components (default=50).")
    parser.add_argument("--ica-method", type=str, default='fastica', help="ICA method (e.g. fastica, infomax).")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed for ICA (default=42).")

    # Trial-related optional argument
    # "do_trial" can be triggered either by: "TRIAL" in commands or by passing --do-trial
    parser.add_argument(
        "--do-trial",
        action="store_true",
        default=False,
        help="True: generate trials after Preprocessing. Can also be triggered by 'TRIAL' command."
    )

    args = parser.parse_args()
    commands_lower = [cmd.lower() for cmd in args.commands]

    # Identify which channels to process
    channel_set = set()
    if 'meeg' in commands_lower:
        channel_set.update(['mag', 'grad', 'eeg'])
    if 'meg' in commands_lower:
        channel_set.update(['mag', 'grad'])
    if 'mag' in commands_lower:
        channel_set.add('mag')
    if 'grad' in commands_lower:
        channel_set.add('grad')
    if 'eeg' in commands_lower:
        channel_set.add('eeg')

    # If "ICA" alone → default to MEEG
    if (len(channel_set) == 0) and ('ica' in commands_lower) and (len(commands_lower) == 1):
        print("No channel commands specified but ICA is present --> Default to MEEG channels [Mag, Grad, EEG].")
        channel_set.update(['mag', 'grad', 'eeg'])
    
    # If no commands at all, just exit
    if not commands_lower:
        print("No commands provided. Exiting. Possible commands: MEEG, MEG, EEG, MAG, GRAD, ICA, TRIAL, SAMPLE, etc.")
        return

    channel_types_to_process = sorted(list(channel_set))

    do_ica = ('ica' in commands_lower)
    do_trial = args.do_trial or ('trial' in commands_lower) or ('trials' in commands_lower)

    data_dir = config.data_dir
    trials_dir = config.trials_dir
    ica_dir = config.ica_dir

    # 1) Preprocess, generate trial files or ICAs if within command
    if channel_types_to_process:
        preprocess_and_make_trials(
            data_dir=data_dir,
            trials_dir=trials_dir,
            ica_dir=ica_dir,
            channel_types=channel_types_to_process,
            do_ica=do_ica,
            do_trial=do_trial,        
            l_freq=args.l_freq,
            h_freq=args.h_freq,
            notch_freq=args.notch_freq,
            n_versions=args.n_versions,
            trials_per_file=args.trials_per_file,
            total_channels=args.total_channels,
            max_bad_channels=args.max_bad_ch,
            min_bad_channels=args.min_bad_ch,
            n_components=args.n_components,
            ica_method=args.ica_method,
            random_state=args.random_state
        )

if __name__ == "__main__":
    main()
