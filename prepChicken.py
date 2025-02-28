# prepChicken.py
# This script is just for the parser check preproc_funcs.py for specification
import os
import argparse
import config
import json
from chickencode.preproc_funcs import (
    prepare_chickenrun,
    get_unique_path
)

def main():
    parser = argparse.ArgumentParser(
        description="Script to preprocess MEEG data, optionally run ICA, and/or make answer templates."
    )

    # Positional arguments: commands (case-insensitive)
    # e.g. python preproc.py MEEG ICA
    parser.add_argument(
        "commands", 
        nargs="*", 
        help=(
            "Commands: PRE/PREPROC/PREPROCESSING, MEEG, MEG, EEG, MAG, GRAD, ANS, ICA. "
            "Any presence of PRE* triggers preprocessing, "
            "ICA triggers ICA,"
              "PRE/PREPROC/PREPROCESSING trigger preprocessing."
            "ALL: PRE, MEEG, ICA, pickbadchannels, pickbadcomponents"
        )
    )
    # Dataset name (default=dataset1 if user doesn't supply anything)
    parser.add_argument(
        "--data-file",
        type=str,
        default=None,
        help="Name of the dataset to process. (default=None), meaning you go through all datasets in raw/"
    )

    # Common optional arguments
    parser.add_argument("--l-freq", type=float, default=config.l_freq, help="High-pass filter cutoff (default=0.1 Hz).")
    parser.add_argument("--h-freq", type=float, default=config.h_freq, help="Low-pass filter cutoff (default=80 Hz).")
    parser.add_argument("--notch-freq", type=float, default=config.notch_freq, help="Base notch filter frequency (default=50 Hz).")

    parser.add_argument("--total-channels", type=int, default=config.total_channels, help="Number of channels in each snippet (default=15).")
    parser.add_argument("--max-bad-ch", type=int, default=config.max_bad_ch, help="Max bad channels forced in snippet (default=3).")
    parser.add_argument("--min-bad-ch", type=int, default=config.min_bad_ch, help="Min bad channels forced in snippet (default=1).")

    # ICA-related optional arguments
    parser.add_argument("--n-components", type=int, default=config.ica_components, help="Number of ICA components (default=50).")
    parser.add_argument("--ica-method", type=str, default=config.ica_method, help="ICA method (e.g. fastica, infomax).")
    parser.add_argument("--random-state", type=int, default=config.ica_seed, help="Random seed for ICA (default=42).")

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

    # If "ICA" alone, default to MEEG
    if len(channel_set) == 0:
        print("[INFO]No channel commands specified but ICA is present --> Default to MEEG channels [Mag, Grad, EEG].")
        channel_set.update(['mag', 'grad', 'eeg'])
    
    # If no commands at all, just exit
    if not commands_lower:
            print("Commands: PRE/PREPROC/PREPROCESSING, MEEG, MEG, EEG, MAG, GRAD, ICA, TRIAL(S). \n"
            "Any presence of PRE* triggers preprocessing, \n"
            "ICA triggers ICA, TRIAL triggers trial generation,\n")
            return

    channel_types_to_process = sorted(list(channel_set))
    do_preprocessing = any(cmd in ["pre", "preproc", "preprocessing"] for cmd in commands_lower)
    do_ica = ('ica' in commands_lower)
    do_ans = ('pickbadchannels' in commands_lower or 'pickbadcomponents' in commands_lower)
    pick_bad_channels = ('pickbadchannels' in commands_lower)
    pick_bad_components = ('pickbadcomponents' in commands_lower)
    raw_dir = config.raw_dir

    if 'all' in commands_lower:
        do_preprocessing = True
        do_ica = True
        do_ans = True
        pick_bad_channels = True
        pick_bad_components = True     

    # If ICA but no PRE, ask to confirm
    if do_ica and not do_preprocessing:
        resp = input(
            "You specified ICA but not PREPROCESSING. Proceed without preprocessing? [y/n]: "
        ).strip().lower()
        if resp not in ["y", "yes"]:
            do_preprocessing = True  # run the whole process if user says no
    elif do_ans and not do_preprocessing:
        resp = input(
            "You specified ANS but not PREPROCESSING. Proceed without preprocessing? [y/n]: "
        ).strip().lower()
        if resp not in ["y", "yes"]:
            do_preprocessing = True  # run the whole process if user says no
  

    #check which datasets are available if no dataset name is given
    if args.data_file is None:
        datafilenames = [
            f for f in os.listdir(raw_dir) 
            if not f.startswith('.') # skip hidden files
        ]
        if not datafilenames:
            print(f"No datasets found in {raw_dir}. Exiting.")
            return
        print("Available datasets:")
        for i, data_file in enumerate(datafilenames):
            print(f"{i+1}. {data_file}")
    else:
        datafilenames = [args.data_file]

    for data_file in datafilenames:    
        answer_dir = os.path.join("data", "answer") # hardcoding data/answer because let's just don't change this please
        if not os.path.isdir(answer_dir):
            print(f"[ERROR] No 'answer' directory found at {answer_dir}. Exiting.")
            return
        
        # List possible JSON files
        answer_candidates = [f for f in os.listdir(answer_dir) if  f.startswith(data_file[:-3])]
        
        if  do_ans:
            if answer_candidates:
                print("\n there is already an answer file available for this dataset:")
                for ansf in answer_candidates:
                    print(f"  - {ansf}")
                print("\n Do you want to overwrite, reuse or add to the existing answer file? o/r/a]")

                ans = input().strip().lower()
                if ans == 'o':
                    print("Overwriting the existing answer file")         
                    # Create an empty JSON file
                    with open(os.path.join(config.answer_dir, answer_candidates[0]), "w") as file:
                        json.dump({}, file)  # Write an empty dictionary to the file
                    answer_file = answer_candidates[0]
                elif ans == 'a':
                    print("Adding to the existing answer file")
                    answer_file = answer_candidates[0]
                elif ans == 'r':
                    print("Not creating a new answer file")
                    answer_file = None
                    do_ans = False
            else:
                answer_file = data_file[:-3] + "json"
                json.dump({}, open(os.path.join(answer_dir, answer_file), "w"))  # Write an empty dictionary to the file                
        else: # if user did not ask for making an answer file, skip
            answer_file = None
            print("Warning: no answer file will be created")

        #list possible ica files
        ica_candidates = []        
        for root, _, files in os.walk(config.ica_dir):    
            for file in files:   
                if file.startswith(data_file[:-4]):
                    ica_candidates.append(os.path.join(root,file))

        if ica_candidates and 'ica' in commands_lower:
            print("\n Do want to overwrite the existing ica file? [y/n]. \"No\" reuses the existing ica file")
            ans = input().strip().lower()
            
            if ans == 'y':
                print("Overwriting the existing ica file")         
                # Create an empty JSON file
                for file in ica_candidates:                   
                    os.remove(file)
                    ica_candidates = []
            elif ans == 'n':
                print("Reusing the existing ica file")
                do_ica = False
        if (not ica_candidates) and  (not 'ica' in commands_lower):
            print("No ICA file available yet, do you want to make one? [y/n]")
            ans = input().strip().lower()            
            if ans == 'y':
                print("Creating a new ica file")
                do_ica = True
            elif ans == 'n':
                print("ICA file required, exiting")
                return
   # 1) Preprocess, generate trial files or ICAs if within command
        if channel_types_to_process:
            prepare_chickenrun(
                raw_dir=raw_dir,
                data_file=data_file,
                answer_file=answer_file,
                channel_types=channel_types_to_process,
                do_preprocessing = do_preprocessing,
                do_ica=do_ica,
                do_ans = do_ans,
                pick_bad_channels = pick_bad_channels,
                pick_bad_components = pick_bad_components,        
                l_freq=args.l_freq,
                h_freq=args.h_freq,
                notch_freq=args.notch_freq,
                total_channels=args.total_channels,
                max_bad_channels=args.max_bad_ch,
                min_bad_channels=args.min_bad_ch,
                n_components=args.n_components,
                ica_method=args.ica_method,
                random_state=args.random_state,
                
            )

if __name__ == "__main__":
    main()
