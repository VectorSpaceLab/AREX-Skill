# MNE command-line reference

MNE-Python exposes one console script named `mne`. The entry point dispatches as `mne <command> [options]`; command names use underscores, not hyphens. Running `mne` or `mne --help` prints the accepted commands; running `mne --version` prints the installed MNE-Python version.

Source evidence: `pyproject.toml` console script metadata, `mne/commands/utils.py`, `mne/commands/mne_*.py`, `mne/commands/tests/test_commands.py`, installed CLI smoke output.

## Discovery and help patterns

Use these before any command that reads user data, writes files, opens a GUI, invokes FreeSurfer/MNE-C tools, or may scan large folders:

```bash
mne --help
mne --version
mne sys_info --help
mne sys_info --no-check-version --ascii
mne what --help
mne show_info --help
mne report --help
mne setup_source_space --help
mne setup_forward_model --help
```

Rules of thumb:

- `mne <command> --help` is the safest way to inspect options; tests assert that command help prints a `Usage:` line.
- Use `--no-check-version` with `mne sys_info` when network access is disabled or you need deterministic diagnostics.
- Use `--ascii` with `mne sys_info` when logs must be plain ASCII.
- The CLI parser is `optparse` based; many commands accept `--version` and `-h/--help` automatically.
- Invalid top-level command names print `Invalid command: "..."` plus the accepted command list. Prefer correcting the command name over guessing a Python API call.

## Command list and route hints

| Command | Primary purpose | Safe-use notes and likely owner |
| --- | --- | --- |
| `anonymize` | Anonymize a raw FIF file. | File-writing command; inspect `--help`, choose input/output FIF paths, and preserve originals. Detailed raw-file handling belongs to `io-raw-data`. |
| `browse_raw` | Browse raw data interactively. | GUI/display command; inspect help and route backend/display troubleshooting to `visualization-reporting` when plotting details matter. |
| `bti2fiff` | Convert BTi / 4D Magnes data to FIF. | Conversion command; verify required source files and output path. Detailed format decisions belong to `io-raw-data`. |
| `clean_eog_ecg` | Clean EOG/ECG artifacts with SSP/PCA-style projection workflows. | Writes projection/event outputs near the raw input; detailed artifact-cleaning choices belong to `preprocessing-epochs-evoked`. |
| `compare_fiff` | Compare two FIF files. | Read-only comparison of two FIF paths, but it invokes visualization output; use for triage, not as a data-processing step. |
| `compute_proj_ecg` | Compute ECG SSP projections. | Processing command that can write projections/events; route method choices to `preprocessing-epochs-evoked`. |
| `compute_proj_eog` | Compute EOG SSP projections. | Processing command that can write projections/events; route method choices to `preprocessing-epochs-evoked`. |
| `coreg` | Open the coregistration GUI. | GUI plus anatomical data workflow; route source/anatomy logic to `source-modeling-inverse` and display failures to `visualization-reporting`. |
| `flash_bem` | Create 3-layer BEM surfaces from Flash MRI images. | Requires MRI inputs and often FreeSurfer-style anatomy; may write surfaces. Route modeling details to `source-modeling-inverse`. |
| `freeview_bem_surfaces` | View BEM surfaces using Freeview. | External GUI/viewer workflow; check Freeview availability and route anatomy details to `source-modeling-inverse`. |
| `kit2fiff` | Convert KIT / NYU data to FIF. | Conversion command; verify marker/head-shape/slope/stim options from help before running. |
| `make_scalp_surfaces` | Create head/scalp surfaces for coordinate alignment. | Writes surfaces under a subjects directory; can require FreeSurfer and optional visualization dependencies. |
| `prepare_bem_model` | Create a BEM solution from a BEM model. | Writes BEM solution FIF; route numerical/source-modeling decisions to `source-modeling-inverse`. |
| `report` | Create an HTML MNE report for a folder. | Scans a folder and writes HTML; use `--no-browser` for headless runs, set `--overwrite` deliberately, and pass `--info`, `--subject`, `--subjects-dir`, or `--cov` only when needed. |
| `setup_forward_model` | Create BEM model and solution for a subject. | Writes model/solution files; requires anatomy inputs and conductivity/spacing decisions. Route to `source-modeling-inverse`. |
| `setup_source_space` | Create a bilateral hemisphere source space. | Writes source-space FIF; check mutually exclusive spacing flags (`--spacing`, `--ico`, `--oct`) in help. Route to `source-modeling-inverse`. |
| `show_fiff` | Show contents of a FIF file. | Read-only inspection. Use `--tag` for focused tag output when help confirms the option. |
| `show_info` | Show measurement info from a `.fif` file. | Read-only; command rejects non-`.fif` filenames. Detailed `Info` interpretation belongs to `io-raw-data`. |
| `surf2bem` | Convert a surface to BEM FIF. | File conversion that writes a BEM FIF; route anatomy/modeling assumptions to `source-modeling-inverse`. |
| `sys_info` | Show platform, Python, MNE, and dependency information. | Use `--no-check-version` to avoid remote latest-version checks; use `--developer` only when maintainer dependency detail is needed. |
| `watershed_bem` | Create BEM surfaces with the FreeSurfer watershed algorithm. | External FreeSurfer workflow; can overwrite or create anatomy outputs. Route modeling details to `source-modeling-inverse`. |
| `what` | Check the type of FIF file(s). | Read-only; prints type labels such as `raw` for recognized FIF files. |

## Safe command recipes

### Inspect installed MNE without network

```bash
mne --version
mne sys_info --no-check-version --ascii
```

Expected observations: the version command prints `MNE <version>`; `sys_info` prints platform, Python, CPU/memory, core dependencies, and optional-dependency availability. If `mne sys_info` is too verbose, use Python `mne.sys_info(check_version=False)` and write to a file-like object in the active session.

### Inspect a FIF file without modifying it

```bash
mne what sample_raw.fif
mne show_info sample_raw.fif
mne show_fiff --help
```

Expected observations: `what` prints an object type when the FIF is recognized; `show_info` prints `File : ...` plus an `Info` summary. If the task requires reading non-FIF formats or making sense of channel metadata, route to `io-raw-data`.

### Build a report in a headless environment

```bash
mne report --path MNE-sample-data --no-browser --overwrite --verbose
```

Before running, verify the folder contains files with MNE naming conventions such as `-raw.fif`, `-epo.fif`, `-ave.fif`, `-cov.fif`, `-trans.fif`, `-fwd.fif`, or `-inv.fif`. Add `--info`, `--subject`, `--subjects-dir`, and `--cov` only when report content needs those objects. Route plot rendering and report API customization to `visualization-reporting`.

### Probe help through the bundled helper

From this sub-skill directory:

```bash
python scripts/mne_cli_probe.py --commands sys_info what show_info report --strict
```

This runs help/version probes only by default. Add no-download dataset checks with an explicit cache root:

```bash
python scripts/mne_cli_probe.py --dataset-check sample testing --dataset-path PATH_TO_MNE_DATA --strict
```
