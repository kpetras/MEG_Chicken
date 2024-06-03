# MEG_Chicken

# EEG and MEG Data Classification Experiment

This repository contains the code and resources for an EEG and MEG data classification experiment. The experiment involves preprocessing EEG and MEG data, fitting Independent Component Analysis (ICA) models, preparing trials, and running an experiment with both control and experimental groups.

## Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [Usage](#usage)
  - [Preprocessing](#preprocessing)
  - [Preparing Trials](#preparing-trials)
  - [Running the Experiment](#running-the-experiment)
- [Experiment Details](#experiment-details)
- [Results](#results)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Introduction

This experiment is designed to classify and identify artifacts in EEG and MEG data recordings. Participants are divided into two groups: the experimental group receives feedback during the task, while the control group does not. The primary goal is to evaluate the effectiveness of feedback in improving artifact detection accuracy.

## Installation

### Clone the Repository

```bash
git clone https://github.com/yourusername/EEG-MEG-Classification-Experiment.git
cd EEG-MEG-Classification-Experiment

### Set Up the Environment

## Usage

### Preprocessing
The preprocessing.py script handles loading and preprocessing of raw EEG and MEG data, including applying filters and fitting ICA models.

### Running Preprocessing

Define the path to the raw data in preprocessing.py.
List the files to preprocess.
Run the preprocessing script:

```bash
python preprocessing.py

### Preparing Trials
The prepare_trials.py script prepares trial data for the experiment by selecting and shuffling channels, and storing the prepared data.

### Running Trial Preparation

Ensure the preprocessed data is available in the specified directory.
Run the trial preparation script:

```bash
python prepare_trials.py

### Running the Experiment
There are separate scripts for the experimental and control groups:

chickenrunChannel_exp.py for the experimental group
chickenrunChannel_ctrl.py for the control group
Running the Experimental Group Script

```bash
python chickenrunChannel_exp.py

```bash
python chickenrunChannel_ctrl.py

### Experiment Details

Objective: To classify and identify artifacts in EEG and MEG data recordings.
Methodology: Participants are shown EEG and MEG recordings and asked to identify channels contaminated by artifacts. Feedback is provided to the experimental group.
Data: Preprocessed EEG and MEG recordings from multiple subjects and sessions.
Analysis: Accuracy of artifact detection is measured and compared between the experimental and control groups.

### Results

Results are saved as CSV files in the experimental/channel_results and control/channel_results directories, including metrics such as hits, false alarms, misses, and correct rejections.

### License

This project is licensed under the MIT License - see the LICENSE file for details.

### Acknowledgements

Special thanks to the contributors for their support and resources.

