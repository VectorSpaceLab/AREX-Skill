# CLI, dataset, config, and install troubleshooting

Use this page to turn symptoms into bounded checks and recovery actions. Route scientific workflow decisions to the owning analysis sub-skill after the environment, command, dataset, or config issue is understood.

Source evidence: command dispatch code, command tests, dataset fetch utilities and tests, config/logging utilities and tests, install documentation, and installed CLI smoke evidence.

## Invalid or missing CLI commands

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Shell says `mne: command not found`. | The environment containing MNE-Python is not active, the console script is not on `PATH`, or MNE was installed into a different Python. | Run `python -c "import mne; print(mne.__version__)"` in the intended Python. If import fails, install MNE into that environment. If import succeeds but `mne` is missing, reinstall with `python -m pip install --force-reinstall mne` or repair the environment's script path. |
| `Invalid command: "..."` plus accepted commands. | Top-level command misspelled or hyphenated. MNE command names use underscores. | Run `mne --help`; use names like `sys_info`, `show_info`, `show_fiff`, `setup_source_space`, and `setup_forward_model`. |
| `mne sys-info` fails. | Hyphen was used instead of underscore. | Use `mne sys_info --help`. |
| A command prints usage and exits. | Required positional files or mutually exclusive options are missing or invalid. | Run `mne <command> --help`; identify required positional arguments and option constraints before retrying. |
| GUI command hangs or display/backend errors appear. | `browse_raw`, `coreg`, Freeview, or visualization/report commands need a display or optional GUI packages. | Use help-only probes first. For report generation in headless runs, add `--no-browser`. Route backend decisions to `visualization-reporting`. |

## `sys_info` surprises

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `mne sys_info` is slow or emits a latest-version warning. | Default version checking queries GitHub. | Use `mne sys_info --no-check-version --ascii` or Python `mne.sys_info(check_version=False, unicode=False)`. |
| Output includes local paths. | `--show-paths` or `show_paths=True` was used. | Treat path output as private triage data. Redact before sharing publicly. |
| Optional packages are listed as unavailable. | The active environment is core/minimal. | Install only the optional family needed by the task, then rerun `sys_info`. Use [installation and extras](installation-and-extras.md) for choices. |

## Missing datasets and offline mode

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `data_path(download=False)` returns a path that prints as `.`. | MNE returned an empty `Path('')` because the dataset is absent or out of date and downloads are disabled. | Treat this as "dataset not available." Do not use `.` as a data root. Ask for a real cache root, allow a download, or switch to a synthetic/no-data workflow. |
| `FileNotFoundError` says the configured `MNE_DATA` path does not exist. | A persistent config or environment variable points to a missing directory. | Create the directory or update `MNE_DATA`/dataset-specific config with `mne.set_config`. Prefer explicit `path=` for scripts. |
| A test or CI run tries to download data. | Dataset helper was called without `download=False`. | In tests and offline probes, pass `download=False, update_path=False`. MNE's tests enforce this pattern for MNE-owned test callers. |
| A dataset helper prompts for path update. | `update_path=None` was used. | Use `update_path=False` for temporary/no-download runs or `update_path=True` when the user explicitly wants persistent config. |
| A fetcher asks for license acceptance. | Some datasets/parcellations require explicit license acceptance. | Only pass `accept=True` when the user has authority and understands the license. Otherwise stop or choose a dataset-free path. |

## Network, cache, and corrupted downloads

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Dataset download fails intermittently. | Network, OSF/GitHub/Zenodo availability, proxy, or timeout issue. | Do not assume code is wrong. Retry later, use an existing cache, or ask the user to provide the dataset root. Keep `download=False` when downloads are forbidden. |
| Hash mismatch or checksum error. | Partial/corrupted cached archive or upstream mirror issue. | If the user permits network access, retry with `force_update=True` for that dataset. Otherwise remove the corrupted cache only with user approval. |
| Disk usage is unexpectedly high. | Full datasets, examples, or reports can be large; `mne report` scans folders and writes HTML/assets. | Use no-download checks, narrow paths, avoid `force_update`, and choose synthetic or testing data where possible. |
| Parallel jobs exhaust memory. | Large arrays without appropriate memmap/cache settings. | Create a cache directory, call `mne.set_cache_dir("PATH_TO_EXISTING_CACHE_DIR")`, and set `mne.set_memmap_min_size("100M")` or another task-appropriate threshold. |

## Config file and permissions

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Config JSON is reported corrupt. | The `mne-python.json` file is not valid JSON. | Use `mne.get_config_path()` to locate it. Back it up, repair valid JSON, or reset affected keys through `mne.set_config` if possible. |
| Config cannot be written. | The `.mne` directory or config file is not writable. | Use environment variables for temporary overrides, fix permissions, or pass explicit function arguments such as `path=` and `subjects_dir=`. |
| A setting appears ignored. | Environment variable overrides the config file. | Check `mne.get_config(key, use_env=True)` and `mne.get_config(key, use_env=False)` to distinguish active env overrides from persisted values. |
| Setting a key warns that it is non-standard. | Key is not in MNE's known config list or wildcard prefixes. | Verify spelling with `mne.get_config("")`. Avoid custom keys unless an extension package documents them. |

## Optional dependencies and extras

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| HDF5/MATLAB-style file reading or saving fails due missing `h5io`, `h5py`, or `pymatreader`. | Core install lacks HDF5 extras. | Install `mne[hdf5]` or equivalent packages, then rerun `mne sys_info --no-check-version`. |
| 3D plotting, browser, or coregistration import fails. | Qt/PyVista/VTK/browser dependencies or display backend missing. | Install only the needed visualization extras. In headless contexts use non-interactive routes and `--no-browser`; route details to `visualization-reporting`. |
| Source modeling command fails because FreeSurfer/OpenMEEG is absent. | External binaries are not part of core MNE-Python. | Confirm whether the task truly needs those binaries. Route modeling prerequisites to `source-modeling-inverse`. |
| Decoding estimator workflow fails due missing scikit-learn. | Decoding extras are optional. | Install scikit-learn or choose an analysis path that does not use decoding estimators. |
| CUDA acceleration is unavailable. | CuPy, NVIDIA driver, or `MNE_USE_CUDA` setup is missing. | Treat CUDA as optional unless the task explicitly requires it. Verify with `mne.cuda.init_cuda(verbose=True)` only after installing compatible CUDA/CuPy components. |
