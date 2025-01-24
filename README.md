![Banner](banner.png)
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

### Preprocessing with preproc.py
The preproc.py script handles loading and preprocessing of raw EEG and MEG data, including applying filters, generating trial files and fitting ICA models.

To generate or regenerate trial data (pickled) on raw data:
```bash
python preproc.py MEEG TRIAL
```
To Run ICA on raw data:
```bash
python preproc.py MEEG ICA
```
For both tasks:
```bash
python preproc.py MEEG ICA TRIAL
```

Options:

`--l-freq`, `--h-freq`, `--notch-freq`: set filter cutoffs.

`--n-components`: for ICA.

`--n-versions`, `--trials-per-file`: how many trial versions to create.

`--do-trial`: explicitly triggers trial generation.

Example:
```bash
python preproc.py MEEG ICA --do-trial --n-components 25 --n-versions 2 --trials-per-file 3
```

### Running the training
```bash
python chickenrun.py
```


## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

### Acknowledgements

Special thanks to the contributors for their support and resources.


