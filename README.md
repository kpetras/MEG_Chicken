![Banner](banner.png)

# MEG_Chicken

This repository contains code and resources for an EEG and MEG artifact detection training program. Trainees can review and annotate data and receive immediate feedback on their choices. Trainers are encouraged to upload their own annotated data.

---

## **1. Environment Setup with `initializeChicken.py`**

Before running any other scripts, **ensure** your environment is ready:

``` bash
python -m pip install -r requirements.txt
python initializeChicken.py
```
- This script checks for required packages (via `requirements.txt`).
- It creates directory structures (e.g., `data/`, `data/raw/`, `data/answer/`, etc.).
- It downloads an MNE sample `.fif` file for demonstration, then removes unneeded files.
---

## **2. Data Structure**

Below is the recommended folder layout. Adjust if needed:
``` graphql
data/
├── raw/                         # Your raw .fif files
├── dataset1/
│   ├── core_data/               # Preprocessed files
│   │   ├── *.fif
│   │   └── index_db/            # Trial index database
│   ├── ica/                     # ICA results by channel type
│   │   └── {channel_type}/
│   └── trials/                  # SQLite DB for trial info
├── answer/                      # JSON files with annotated data (bad channels/ICA comps)
├── session/                     # (Optional) Pickled session files
└── res/                         # (Optional) CSV result files (scores, logs, etc.)


```
---

## **3. Preprocessing with `prepChicken.py`**

`prepChicken.py` applies filtering, ICA fitting, and trial file generation. All raw `.fif` files should follow the naming format: `subject_session_run.fif`.
### **Usage**
``` bash
python prepChicken.py [COMMANDS] [OPTIONS]
```

### **Commands (Case-Insensitive)**

- **Channel Types**:
    
    - `EEG` → Only EEG
    - `MEG` → Mag + Grad
    - `Mag` → Magnetometers only
    - `Grad` → Gradiometers only
    - `MEEG` → All channel types (default if none specified)
- **Process Steps**:
    
    - `PRE` / `PREPROC` / `PREPROCESSING` → Run basic preprocessing (filtering)
    - `ICA` → Fit and save ICA components
    - `TRIAL` / `TRIALS` → Generate trial files in `.db` format
    - `ANS` -> Creating answer sheet for data
    - `ALL` → Shorthand for `PRE + ANS + ICA + TRIAL`

### **Options (Examples)**
``` bash
# Adjust filters or ICA settings on the command line:
python prepChicken.py PRE --l-freq 0.5 --h-freq 60
python prepChicken.py ICA --n-components 30 --ica-method fastica

# Combine multiple steps:
python prepChicken.py MEEG PRE ICA TRIAL --trials-per-file 5
# OR
python prepChicken.py MEEG ALL
```
For additional parameters, see `config.py`.

---
## **4. Start the training with `runChicken.py`**
``` bash
python runChicken.py
```
Launches a graphical interface where trainees can:
1. Enter Participant ID, Session ID.
2. Choose a dataset folder (e.g. `dataset1`) and an answer file (e.g. `data/answer/some_answer.json`).
3. Decide whether to enable immediate feedback, deselect mode, and/or show instructions.
4. Conduct trials in **EEG/MEG mode** or **ICA mode**, selecting channels or components believed to be “bad.”
## 5. Additional Tips
- **Answer File (.json)**: Must exist in `data/answer/` if you want to enable correct/incorrect feedback.
- **Modifying Default Settings**: Check `config.py`.
- **Resuming Sessions**: Unfinished runs are usually saved so you can resume from where you left off.
## Enjoy discovering and labeling artifacts in your EEG/MEG data!