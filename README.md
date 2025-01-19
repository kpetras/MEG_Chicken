# MEG_Chicken

# EEG and MEG artifact detection

This repository contains code and resources for an EEG and MEG artifact detection training program. Trainees can review and annotate data and receive immediate feedback on their choices. Trainers are encouraged to upload their own annotated data.

## Table of Contents

- [Introduction](#introduction)
- [Implicit learning: the chicken sexing problem](#background)
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

## Implicit learning: chicken sexing problem

Chicken sexers quickly and reliably determine the sex of day old chicks that do not have obvious distinguishing features . They do so often without explicit knowledge of the visual cues differentiating male from female chicks. Instead, their skill is developed through implicit procedural learning, facilitated by direct and immediate feedback during training.We here use a similar principle, direct and immediate feedback on each decision, to train researchers to quickly and reliably detect artifacts in MEG and EEG data.
Ref: https://web-archive.southampton.ac.uk/cogprints.org/3255/1/chicken.pdf

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

