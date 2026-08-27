# Installation and Environment

Read this before choosing dependencies or running MNE-Python code in a new
runtime.

## Python and base dependencies

MNE-Python requires Python 3.11 or newer in this checkout. The base package is
installed with:

```bash
pip install mne
# or for development from a checkout
pip install -e .
```

The documented base dependencies include NumPy, SciPy, Matplotlib, Jinja2,
Pooch, lazy-loader, decorator, packaging, and tqdm. Base installs support many
core I/O, Raw/Epochs/Evoked, filtering, 2D plotting, and statistics workflows.

## Optional install choices

| Need | Typical install direction | Notes |
| --- | --- | --- |
| Minimal/core workflows | `pip install mne` or conda-forge `mne-base` | Good for import, many FIF/array workflows, 2D plotting, config, CLI help. |
| HDF5 and MATLAB-like I/O | `pip install "mne[hdf5]"` | Adds HDF5-related packages used by some readers/savers. |
| Broad functionality | `pip install "mne[full]"` or conda-forge `mne` | Pulls many optional readers, 3D/Qt/browser/notebook/data-analysis extras. |
| Full without Qt choice | `pip install "mne[full-no-qt]"` | Useful when the platform already manages Qt or GUI is not needed. |
| Specific Qt binding | `pip install "mne[full-pyside6]"` or `pip install "mne[full-pyqt6]"` | Choose only for GUI/browser workflows that need that binding. |
| Decoding | install scikit-learn or a full extra path | Many `mne.decoding` objects import scikit-learn. |
| 3D/source visualization | PyVista, PyVistaQt/Qt or notebook dependencies | Optional; use headless-safe fallbacks when absent. |
| Anatomy/source modeling | FreeSurfer, OpenMEEG, MNE datasets, or precomputed files | External tools/data, not base Python dependencies. |

Do not install all optional extras by default. Select only the extras required
by the user's workflow and environment.

## Environment checks

Use the bundled smoke helper for a safe CPU check:

```bash
python scripts/mne_smoke_check.py
python scripts/mne_cli_probe.py --strict
```

The helpers avoid downloads, GUI windows, and original repository files. If a
workflow needs a backend not covered by the smoke check, verify that backend
separately before promising execution.

## Dataset and cache policy

MNE dataset helpers can download data via Pooch. In constrained environments:

- call dataset helpers with `download=False` when you only want to test whether
  data are already present;
- avoid mutating persistent config unless the user agrees;
- record cache locations and required disk/network budget before downloading;
- route dataset helper details to `sub-skills/cli-datasets-config`.

## Headless and GUI policy

For scripts and CI:

- use Matplotlib non-interactive backends;
- pass `show=False` and save figures explicitly;
- pass `open_browser=False` to report saving;
- avoid PyVista/Qt/notebook backends unless display/session support exists.

## Source-modeling policy

Source workflows may require MRI/FreeSurfer anatomy, transforms, BEM/source
files, sample/testing datasets, and external commands. Base package import is
not proof that subject-specific source localization can run. Route to
`sub-skills/source-modeling-inverse` and validate inputs first.
