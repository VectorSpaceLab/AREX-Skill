# Datasets, configuration, logging, cache, and system information

Use this reference for MNE-Python support workflows that should be resolved before running scientific analysis: locating example datasets, avoiding accidental downloads, setting persistent config, adjusting logging, recording `sys_info`, and choosing cache/memmap behavior.

Source evidence: `mne/datasets/config.py`, `mne/datasets/utils.py`, `mne/datasets/_fetch.py`, dataset package modules, `mne/utils/config.py`, `mne/utils/_logging.py`, `mne/datasets/tests/test_datasets.py`, `mne/utils/tests/test_config.py`, `mne/utils/tests/test_logging.py`, installed API and CLI smoke evidence.

## Dataset path model

Most MNE-supplied datasets expose a helper like:

```python
from mne.datasets import sample, testing, misc

sample_path = sample.data_path(
    path=None,
    force_update=False,
    update_path=True,
    download=True,
)
```

Common arguments:

- `path`: explicit root directory to search or download into. Passing this is the most reproducible choice for scripts.
- `force_update`: redownload/update even if a local copy exists.
- `update_path`: whether to store the root in MNE config. Use `False` for tests, temporary scripts, CI probes, and no-download checks. Use `True` only when the user wants a persistent default. Avoid `None` in non-interactive runs because it may prompt.
- `download`: set `False` to assert that no network download should happen. If the dataset is absent or out of date, MNE returns an empty `Path` result (`Path('')`, which often stringifies as `'.'`). Treat that as "not locally available," not as the current working directory.
- `verbose`: follows the usual MNE verbosity conventions.

Resolution order when `path is None`:

1. dataset-specific config key such as `MNE_DATASETS_SAMPLE_PATH`, if defined;
2. general `MNE_DATA` config key;
3. default `~/mne_data` directory.

If a configured `MNE_DATA` path does not exist, MNE raises `FileNotFoundError` and asks the user to create the directory or set `MNE_DATA` to an existing location. If no path/config exists, MNE may create the default data root before it can decide whether a dataset is present.

## No-download dataset checks

Use these patterns whenever the task is planning, testing, or running offline:

```python
from pathlib import Path
from mne.datasets import sample, testing

root = Path("PATH_TO_MNE_DATA")
path = sample.data_path(path=root, download=False, update_path=False)
if str(path) == ".":
    print("sample dataset is not available under root")
else:
    print(f"sample dataset found at {path}")

# Testing dataset checks should also disable downloads.
testing_path = testing.data_path(path=root, download=False, update_path=False)
```

Notes:

- In MNE's own tests, dataset helpers are expected to pass `download=False` to prevent accidental downloads.
- `mne.datasets.has_dataset(name)` can check presence for supported datasets, but it still follows MNE path resolution and can raise if configured paths are invalid. For strict offline probes, prefer an explicit `path=...` plus `download=False`.
- Dataset-specific helpers may add parameters. Examples include `hf_sef.data_path(dataset="evoked" | "raw")`, `limo.data_path(subject=...)`, `eegbci.load_data(subjects=..., runs=...)`, and `sleep_physionet` fetchers. Check the helper's Python signature before assuming the generic pattern.
- Some fetchers have license prompts or acceptance flags (`accept=True` for selected resources). Only accept licenses when the user has authority to do so.

## Useful dataset/config keys

| Key | Purpose |
| --- | --- |
| `MNE_DATA` | General MNE data root used when a dataset-specific key is not set. |
| `MNE_DATASETS_SAMPLE_PATH`, `MNE_DATASETS_TESTING_PATH`, `MNE_DATASETS_MISC_PATH`, and other `MNE_DATASETS_*_PATH` keys | Dataset-specific roots. Prefer these for persistent cache locations of named datasets. |
| `SUBJECTS_DIR` | FreeSurfer/MRI subjects directory used by source modeling, BEM, coregistration, and anatomy helpers. |
| `MNE_LOGGING_LEVEL` | Default MNE log verbosity when `verbose=None`. |
| `MNE_CACHE_DIR` | Joblib cache/memmap directory for parallel computations. The directory must already exist before setting it. |
| `MNE_MEMMAP_MIN_SIZE` | Minimum array size that triggers memmapping, using suffixes such as `100K`, `500M`, or `1G`; `None` disables. |
| `MNE_BROWSER_BACKEND`, `MNE_BROWSER_*`, `MNE_3D_OPTION_*` | Visualization/browser settings; route display-specific troubleshooting to `visualization-reporting`. |
| `MNE_USE_CUDA`, `MNE_CUDA_DEVICE` | Optional CUDA acceleration settings; route numerical workflow choices to the relevant analysis sub-skill. |

## Config API patterns

Prefer public config helpers over editing JSON:

```python
import mne

config_path = mne.get_config_path()
all_known_keys = mne.get_config("")      # valid key metadata
active_values = mne.get_config(None)      # file values plus env overrides
sample_root = mne.get_config("MNE_DATASETS_SAMPLE_PATH")

mne.set_config("MNE_DATA", "PATH_TO_MNE_DATA", set_env=True)
mne.set_config("MNE_DATA", None, set_env=True)  # delete key
```

Important behavior:

- `get_config(key, use_env=True)` checks environment variables before the config file. Use `use_env=False` when you need only the persisted config file value.
- `get_config(key, raise_error=True)` raises a message that names both environment and config-file remedies when a key is absent.
- `set_config(key, value, set_env=True)` updates both the config file and the current process environment by default. Set `set_env=False` for persistent-only changes.
- Setting a key outside MNE's known key list is allowed but warns. Avoid inventing keys unless an extension package documents them.
- The standard config file is named `mne-python.json` under the user's `.mne` directory. On Windows it is under the user profile; on other systems it is under the home directory.

## Logging and verbosity

MNE uses a package logger named `mne`. Most public functions accept `verbose=None`, and many CLI commands expose `--verbose`.

```python
import mne
from mne import use_log_level

mne.set_log_level("WARNING")  # or "DEBUG", "INFO", "ERROR", "CRITICAL"
old = mne.set_log_level(True, return_old_level=True)  # True means INFO
mne.set_log_level(old)

with use_log_level("INFO"):
    ...
```

Conventions:

- `verbose=True` maps to `INFO`; `verbose=False` maps to `WARNING`.
- If `verbose=None`, MNE reads `MNE_LOGGING_LEVEL`; if unset, it defaults to `INFO`.
- Use `mne.set_log_file(fname, overwrite=True)` only when the user asked for a persistent log file; otherwise logs go to stdout/stderr handlers.

## Cache and memmap settings

Use cache/memmap settings when large arrays and parallel computations are memory-sensitive:

```python
import mne

mne.set_cache_dir("PATH_TO_EXISTING_CACHE_DIR")
mne.set_memmap_min_size("100M")
```

Checks:

- `set_cache_dir()` requires an existing directory; create it explicitly first.
- `set_memmap_min_size()` accepts strings ending in `K`, `M`, or `G`, or `None` to disable. Values like `0.5G` are documented examples; invalid suffixes raise `ValueError`.
- For one-off scripts, prefer process-local environment variables or explicit function arguments over changing a user's persistent config.

## `sys_info` patterns

Use `sys_info` at the start of environment triage:

```python
import io
import mne

mne.sys_info(check_version=False, unicode=False)

buf = io.StringIO()
mne.sys_info(fid=buf, show_paths=False, dependencies="user", check_version=False)
text = buf.getvalue()
```

Options and observations:

- `dependencies="user"` lists core, numerical, visualization, and ecosystem optional packages. `dependencies="developer"` adds testing, documentation, and infrastructure packages.
- `show_paths=True` prints module paths. This is useful for private path-collision debugging but can expose local paths.
- `check_version=True` queries the latest MNE-Python release from GitHub. Disable it for offline, deterministic, or sandboxed runs.
- CLI equivalent: `mne sys_info --no-check-version --ascii`; add `--developer` or `--show-paths` only when needed.
