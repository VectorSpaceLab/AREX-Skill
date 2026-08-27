---
name: mne-python
description: "Route MNE-Python neurophysiology I/O, preprocessing,
  visualization, source modeling, analysis, CLI, datasets, and
  repository-development workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# MNE-Python repo skill

Use this skill when a task involves MNE-Python: MEG/EEG/iEEG/fNIRS/eye-tracking
I/O, Raw/Epochs/Evoked objects, preprocessing, source localization,
time-frequency analysis, statistics, decoding, visualization, reports, datasets,
CLI commands, or safe repository maintenance.

## Start here

1. Confirm MNE-Python is importable and record its version:
   `python -c "import mne; print(mne.__version__)"`.
2. For install choices, optional extras, Python requirements, and environment
   checks, read [references/installation-and-environment.md](references/installation-and-environment.md).
3. For a package map and high-level object relationships, read
   [references/package-map.md](references/package-map.md).
4. If an error spans install, imports, optional dependencies, data/cache,
   plotting backends, or runtime state, read
   [references/troubleshooting.md](references/troubleshooting.md).
5. To smoke-test an environment without datasets or GUI, run
   [scripts/mne_smoke_check.py](scripts/mne_smoke_check.py). For CLI help and
   command discovery, run [scripts/mne_cli_probe.py](scripts/mne_cli_probe.py).
6. To check staleness against a checkout, read
   [references/repo-provenance.md](references/repo-provenance.md).

## Route by task

- **File I/O, Raw, Info, channels, reader selection, array-to-Raw, preload, and
  vendor formats** → `sub-skills/io-raw-data/SKILL.md`.
- **Events, annotations, filtering, bad channels, ICA/SSP, artifact correction,
  Epochs, Evoked, covariance, and rank** →
  `sub-skills/preprocessing-epochs-evoked/SKILL.md`.
- **Plots, topomaps, interactive/headless visualization, 3D backend choices, and
  `mne.Report`** → `sub-skills/visualization-reporting/SKILL.md`.
- **Source spaces, BEM, transforms, forward models, inverse operators,
  beamformers, dipoles, source estimates, labels, and morphing** →
  `sub-skills/source-modeling-inverse/SKILL.md`.
- **PSD, TFR/CSD, cluster statistics, regression, decoding, scikit-learn
  estimators, and simulation** →
  `sub-skills/timefreq-stats-decoding-simulation/SKILL.md`.
- **`mne` CLI commands, dataset helpers, config/cache/logging/sys_info, and
  install extras** → `sub-skills/cli-datasets-config/SKILL.md`.
- **Editing this repository, public API stubs, docs, tests, changelog fragments,
  import-location checks, deprecations, and AI-assistance policy** →
  `sub-skills/repo-development/SKILL.md`.

## Cross-cutting operating rules

- Prefer documented MNE containers and methods over ad-hoc arrays. Track object
  type, channel names/types, sampling frequency, event ids, bad channels,
  projectors, rank, and units at every stage.
- Many MNE object methods mutate in place and return `self`; make copies when
  preserving earlier states matters.
- Optional dependencies are workflow-specific. Base MNE covers many 2D/core
  workflows; HDF5/vendor readers, decoding, 3D/Qt/browser rendering, notebook
  interactivity, FreeSurfer/OpenMEEG, and large datasets require extra checks.
- Do not trigger dataset downloads, GUI windows, FreeSurfer/OpenMEEG commands,
  GPU/CUDA paths, or long examples unless the user explicitly approves those
  resources and runtime side effects.
- When creating code for headless or CI environments, use `show=False`, explicit
  output files, `open_browser=False`, deterministic random seeds, and small
  synthetic data.
- This generated skill is self-contained. Do not require the original
  MNE-Python checkout to be present except when the user explicitly asks for
  repository-development work in a checkout.

## Minimal smoke command

```bash
python scripts/mne_smoke_check.py --include-decoding
```

The smoke helper constructs tiny synthetic data, exercises Raw/Epochs/Evoked,
PSD, imports selected subpackages, optionally checks decoding imports, and never
uses network, datasets, GUI, or source-repository files.
