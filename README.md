# MEG_Chicken

# EEG and MEG artifact detection

This repository contains code and resources for an EEG and MEG artifact detection training program. Trainees can review and annotate data and receive immediate feedback on their choices. Trainers are encouraged to upload their own annotated data.

## Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [Usage](#usage)
  - [Preprocessing](#preprocessing)
  - [Preparing Trials](#preparing-trials)
  - [Running the Experiment](#running-the-experiment)
- [Experiment Details](#experiment-details)
- [Results](#results)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Introduction

The detection of physiological and non-physiological artifacts in M/EEG data is notoriously subjective and relies on rigorous training. Here, we provide a simple tool, based on visualizations provided through MNE python, to train students to consistently detect different types of artifacts and real M/EEG data.
## Installation

### Clone the Repository

```bash
git clone https://github.com/yourusername/MEG_Chicken.git
cd MEG_Chicken
```

### Set Up the Environment

## Usage

### Preprocessing
The preprocessing.py script handles loading and preprocessing of raw EEG and MEG data, including applying filters and fitting ICA models.

### Running Preprocessing

- Define the path to the raw data in `preprocessing.py`.
- List the files to preprocess.
- Run the preprocessing script:
```bash
python preprocessing.py
```

### Preparing Trials
The prepare_trials.py script prepares trial data for the experiment by selecting and shuffling channels, and storing the prepared data.

### Running Trial Preparation

- Ensure the preprocessed data is available in the specified directory.
- Run the trial preparation script:

```bash
python prepare_trials.py
```
### Running the training
```bash
python chickenrun.py
```


## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

### Acknowledgements

Special thanks to the contributors for their support and resources.

