# Configuration, Weights, Licenses, and Offline Use

TotalSegmentator stores runtime state under a TotalSegmentator home directory and resolves nnU-Net model weights from a weights directory. These settings affect downloads, licenses, usage stats, and offline deployment.

## Runtime Directories

Resolution rules from `totalsegmentator.config`:

| Purpose | Default | Override |
| --- | --- | --- |
| TotalSegmentator home | user home `.totalsegmentator` directory; if the home directory resolves to `/`, use `/tmp/.totalsegmentator` | `TOTALSEG_HOME_DIR` |
| Weights directory | `<totalseg_home>/nnunet/results` | `TOTALSEG_WEIGHTS_PATH` |
| Config file | `<totalseg_home>/config.json` | indirectly via `TOTALSEG_HOME_DIR` |

`setup_nnunet()` sets `nnUNet_raw`, `nnUNet_preprocessed`, and `nnUNet_results` for the current Python process. If `TOTALSEG_WEIGHTS_PATH` is set, all three point there; otherwise they point to the default weights directory.

For services, tests, containers, and multi-user systems, set `TOTALSEG_HOME_DIR` to an isolated writable directory before importing/running TotalSegmentator. Set `TOTALSEG_WEIGHTS_PATH` when weights must be shared or mounted separately from config/license state.

Example process-local setup:

```bash
export TOTALSEG_HOME_DIR=<writable-totalseg-home>
export TOTALSEG_WEIGHTS_PATH=<prestaged-nnunet-results>
python scripts/check_totalseg_runtime.py --show-paths --json
```

Do not expose these absolute paths in public logs unless the user explicitly needs path diagnostics.

## `config.json` Schema

`setup_totalseg()` creates `config.json` when missing. Initial keys are:

```json
{
  "totalseg_id": "totalseg_<random>",
  "send_usage_stats": true,
  "prediction_counter": 0
}
```

Additional keys are added over time, including:

- `license_number` after `totalseg_set_license` or API `license_number=...`.
- `statistics_disclaimer_shown` after a run or `totalseg_download_weights`.

Use public helpers when writing config from Python:

```python
from totalsegmentator.config import setup_totalseg, get_config, set_config_key
setup_totalseg()
set_config_key("send_usage_stats", False)
print(get_config())
```

The bundled checker reports only safe config metadata by default and redacts the license value.

## Usage Statistics

TotalSegmentator sends anonymous usage statistics by default when `send_usage_stats` is true. Disable it before running segmentation or helper applications:

```python
from totalsegmentator.config import setup_totalseg, set_config_key
setup_totalseg()
set_config_key("send_usage_stats", False)
```

Or edit `config.json` so `send_usage_stats` is `false`. Prefer the Python helper in automation because it preserves existing keys.

## Weight Download Commands

Normal segmentation downloads missing weights automatically. For image-free provisioning, use:

```bash
totalseg_download_weights -t total
totalseg_download_weights -t total_mr
totalseg_download_weights -t all
```

Important behavior:

- The command calls `setup_totalseg()` and writes `statistics_disclaimer_shown=true`.
- It stores weights under `get_weights_dir()`.
- Licensed model weights require a saved valid license before download.
- `all` downloads every known model id and can be large; use only when the deployment truly needs broad coverage.

`totalseg_import_weights -i weights.zip` extracts a manually downloaded zip into `get_weights_dir()`. The upstream command is marked deprecated for version 2.0.0 and later, but it remains a useful compatibility path for controlled environments with a known zip file.

## Offline Pre-Stage Pattern

Use this sequence for offline systems:

1. On an internet-connected staging machine, install the same TotalSegmentator version expected offline.
2. Set `TOTALSEG_HOME_DIR` and, if desired, `TOTALSEG_WEIGHTS_PATH` to match the directory layout that will be copied or mounted offline.
3. Run `totalseg_download_weights -t <task>` for every required task. For licensed tasks, set the license first.
4. Copy the TotalSegmentator home directory and/or the separate weights directory to the offline target.
5. On the offline target, set `TOTALSEG_HOME_DIR` and `TOTALSEG_WEIGHTS_PATH` to the staged locations.
6. Run `python scripts/check_totalseg_runtime.py --task <task> --offline --json` to verify importability, task license flag, config presence, and weight-directory presence without downloading.

Do not rely on `totalseg_info` alone to prove weights exist: registry discovery is intentionally independent of model files.

## License Setup

Fifteen selectable tasks in TotalSegmentator 2.14.0 require a license. Query live task flags with:

```bash
totalseg_info --list-tasks --json
python scripts/check_totalseg_runtime.py --task heartchambers_highres --json
```

Set a license once per TotalSegmentator home:

```bash
totalseg_set_license -l aca_12345678901234
```

Validation behavior:

- The CLI requires license strings to start with `aca_` and have exactly 18 characters.
- By default, `totalseg_set_license` validates the license against the TotalSegmentator backend before saving it.
- `totalseg_set_license --skip_validation` bypasses the network validation only when the user is sure the license is valid.
- Tests confirm `set_license_number()` skips revalidation when the existing saved license is unchanged, and validates when the saved license changes.
- During segmentation, licensed tasks use an offline shape check via `has_valid_license_offline()`: a saved 18-character license is accepted locally, otherwise the run exits before inference.

Never print or store the real license number in generated reports or shared logs. The bundled checker only reports whether a license is present and whether its shape matches the local offline check.

## Useful Read-Only Diagnostics

```bash
# Full safe registry, no model load
totalseg_info --json

# Runtime state, paths redacted by default
python scripts/check_totalseg_runtime.py --json

# Include paths only for local debugging
python scripts/check_totalseg_runtime.py --show-paths --json

# Validate a licensed task flag and offline license shape without backend validation
python scripts/check_totalseg_runtime.py --task tissue_types --offline --json
```

Use `--show-paths` only in private diagnostic contexts; it intentionally reveals local absolute paths.
