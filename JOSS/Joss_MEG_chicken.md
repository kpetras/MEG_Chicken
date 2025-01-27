---
title: "MEG Chicken: Interactive Artifact Detection Training for MEG and EEG data"

tags:
  - Python
  - MEG
  - EEG
  - Artifact Detection
  - Implicit Learning
  - Feedback

authors:
  - name: Kirsten Petras
    orcid: 0000-0001-5865-921X
    affiliation: 1
    equal-contrib: true 
  - name: Yue Kong
    affiliation: 1
    orcid: 0009-0002-3679-4300
    equal-contrib: true
  - name: Hayley Yingxuan Wu
    affiliation: 1
    orcid: 0009-0009-5750-6591
    equal-contrib: true
  - name: Laura Dugué
    orcid: 0000-0003-3085-1458
    equal-contrib: false
    affiliation: "1, 2"

affiliations:
  - name: Université Paris Cité, INCC UMR 8002, CNRS, F-75006 Paris, France
    index: 1
  - name: Institut Universitaire de France (IUF), Paris, France
    index: 2

date: 17 January 2025

bibliography: references.bib
---

# Statement of Need

Detecting and processing signal artifacts is crucial for analyzing neural time-series data from electroencephalography (EEG) or magnetoencephalography (MEG) recordings [@luck_electroencephalography_2017]. While numerous automated and semi-automated artifact detection algorithms exist e.g.,[@jas_autoreject_2017], visual inspection and manual labeling remain the most widely used methods for identifying components contaminated by eye movements, muscle activity, or electrical noise. Despite excellent resources describing common physiological and electrical artifacts in MEG and EEG data [@burgess_recognizing_2020;@uriguen_eeg_2015], decisions about segment or component rejection are ultimately subjective. This subjectivity often results in inconsistencies, particularly when training new lab members.

Implicit or procedural learning refers to the acquisition of skills and knowledge through repeated exposure and practice, without explicit instruction. A well established example of implicit rule learning is chicken sexing, where workers learn to distinguish the sex of day-old chicks based on subtle visual cues. Despite often not being able to articulate which exact features distinguish between male and female chicks, experienced chicken sexers can classify chicks accurately and reliably through extensive experience and feedback [@horsey_art_nodate]. 

`MEG Chicken` uses the principle of implicit learning through immediate feedback to streamline and standardize the process of learning to detect artifacts in electrophysiology data. The open source software tool presents trainees with data containing various types of artifacts and provides immediate feedback on their decisions, enabling consistent rejection criteria to be learned implicitly. 
Labs can customize the training with their own annotated datasets to ensure alignment with lab-specific standards.

# Functionality

`MEG Chicken` is built on the MNE-Python library and employs MNE's user-friendly graphical interface for visualizing time-series data and sensor topographies. The software includes labeled example datasets available for download via Zenodo, and labs can import or create their own labeled datasets through the interactive interface.

The training program includes modules for:

1. **Bad Channel Rejection**
2. **ICA Component Selection**
3. **Labeled Data Import**
4. **Label Creator**

Participants complete the training at their own pace, progressing until they consistently make correct decisions over a predefined number of trials. The full visualization capabilities of MNE are available in both modules, augmented with information slides.

Immediate feedback after each decision supports implicit learning in the absense of explicit rules.

### Evaluation and Performance

Testing on 5 observes, naive to MEG and EEG artefacts, showed:
- Participants required an average of `xx` minutes to achieve `xx%` accuracy in bad channel selection.
- Participants required an average of `xx` minutes to achieve `xx%` accuracy in ICA component selection.
- Performance remained consistent in follow-up tests conducted several days later.

**Table:**

| Task                   | Average Time to Mastery | Final Accuracy | Retest Accuracy |
|------------------------|-------------------------|----------------|-----------------|
| Bad Channel Rejection  | xx minutes              | xx%            | xx%             |
| ICA Component Selection| xx minutes              | xx%            | xx%             |

# Funding

This project received funding from the European Research Council (ERC) under the European Union’s Horizon 2020 research and innovation program (grant agreement No. 852139 - Laura Dugué).

# Acknowledgments

We thank Laetitia Grabot for providing the example dataset, and Coline Haro for contributions to an earlier version.

# Toolbox Dependencies

- `os`
- `time`
- `random`
- `json`
- `numpy`
- `mne`
- `tkinter`
- `pickle`
- `csv`
- `matplotlib`
- `warnings`
- `scipy`
- `PIL`
- `playsound`
- `copy`

# References
