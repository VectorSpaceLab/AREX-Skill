# Dataset troubleshooting

Diagnose in this order: API/token mismatch, registry selection, expected path,
local format completeness, package version, asset/model prerequisites, then
rendering. Do not start with a broad re-download.

## Registry metadata exists, local dataset does not

**Symptoms**

- `get_ds_meta(...)` returns a mapping with `path`, horizon, and filter key.
- `Path(meta["path"]).exists()` is false.
- A later LeRobot call may try cache/network resolution or fail on missing files.

**Cause**

The registry describes expected dataset locations. It neither downloads nor
validates them.

**Recovery**

```bash
python scripts/plan_dataset_download.py \
  --tasks <ExactTaskName> --split target --source human --require-local
```

If the selection is correct, review the printed dry-run command and storage root.
Run the native downloader only with explicit network/storage approval. Never
turn a registry result into a “dataset available” claim without a local check.

## The target metadata path exists, but it is not a dataset

**Symptoms**

- The expected directory was created manually or by an interrupted extraction.
- `inspect_dataset.py` reports missing `meta/info.json`, `tasks.jsonl`,
  `episodes.jsonl`, or Parquet files.

**Recovery**

Treat the path as incomplete. Preserve any archive or partial directory until its
state is understood. Retry only the selected acquisition after checking free
space and destination. Do not point LeRobot at an empty directory: a directory's
existence is not a readiness signal.

## `task_soup` raises an unexpected-keyword error

**Symptom**

```text
TypeError: get_ds_soup() got an unexpected keyword argument 'task_soup'
```

**Cause**

A documentation example is stale. The live 1.0.1 signature is:

```python
get_ds_soup(split, task_set, source, demo_fraction=1.0)
```

**Recovery**

Use `task_set="atomic_seen"` or another key from `TASK_SET_REGISTRY`. Do not add a
local compatibility shim that hides the mismatch.

## Source spelling differs by API

**Symptoms**

- `get_ds_meta(..., source="mimicgen")` raises `ValueError`.
- The download CLI rejects `--source mg`.

**Cause and recovery**

Use `mg` in `get_ds_meta`/`get_ds_soup`. Use `mimicgen` in
`robocasa.scripts.download_datasets`. `get_ds_path` alone supports `mimicgen` as
an alias. MimicGen dataset availability does not require the optional MimicGen
Python package; generating new synthetic data does, and that package was absent
in the inspected environment.

## `demo_fraction` did not reduce LeRobot samples

**Cause**

The registry only derives `filter_key`; it does not alter the path or filter a
plain `LeRobotDataset` constructor. The LeRobot playback implementation also
rejects `--filter_key`.

**Recovery**

Use a verified training loader that explicitly consumes the filter key or select
a reproducible episode subset yourself. Validate `0 < demo_fraction <= 1` before
querying. Never report a 10% experiment when the loader ignored `50_demos` or
`10_demos`.

## `get_dataset_info` was given HDF5

**Symptoms**

- Errors mention missing LeRobot metadata or dataset construction even though the
  CLI's internal help text says HDF5.

**Cause**

In 1.0.1, `get_dataset_info` constructs `LeRobotDataset(repo_id="robocasa365",
root=...)`. Its stale docstring/help wording is misleading.

**Recovery**

Use it only on the LeRobot root. Use the bundled inspector with an `.hdf5` path
for safe HDF5 structure checks, and the legacy playback CLI for playback.

## HDF5 flags were passed to a LeRobot path

**Symptoms**

- `filter_key not supported for lerobot dataset format`.
- `Not supported with lerobot dataset format currently` after `--use-obs`.
- Absolute-action playback fails or is unavailable.

**Recovery**

Run the matching CLI:

```bash
python -m robocasa.scripts.dataset_scripts.playback_dataset --dataset <lerobot-root>
python -m robocasa.scripts.dataset_scripts.playback_dataset_hdf5 --dataset <demo.hdf5>
```

For LeRobot, use recorded MP4s directly for offline visualization; simulator
playback supports state replay and relative `--use-actions`, not observation-only,
filter-key, or usable absolute-action playback. For HDF5, `--use-obs` is offline
video and cannot combine with either action flag.

## LeRobot sample access fails on videos or decoder

**Symptoms**

- Metadata and Parquet are present, but indexing an image-bearing sample fails.
- Errors mention a missing MP4, codec, or video backend.

**Recovery**

Check `meta/info.json` feature paths against actual `videos/` files. Inspect a
low-dimensional Parquet row if the workflow does not need images. Otherwise
install/configure a decoder compatible with LeRobot 0.3.3 and validate one local
sample in offline mode. Do not allow a local-path typo to trigger remote fetches.

## Simulator replay lacks extras

**Symptoms**

- Missing `extras/dataset_meta.json`.
- Missing `ep_meta.json`, `model.xml.gz`, or `states.npz`.
- `No parquet file found for episode ...`.

**Cause**

The tree may be training-ready but not RoboCasa-replay-ready, or episode numbering
between `extras/` and Parquet may be inconsistent.

**Recovery**

Run the bundled inspector. Verify all episode indices and required files, not just
episode zero. Reacquire or regenerate extras from a trusted source; do not invent
model XML or raw states from aggregate metadata.

## Model XML exists, but replay/reset still fails

**Symptoms**

- Fixture/object XML or mesh/texture files cannot be opened.
- Direct environment construction succeeds, but reset fails.
- MuJoCo reports unresolved assets or malformed/incompatible XML.

**Cause**

Episode `model.xml.gz` does not bundle every referenced kitchen fixture/object
asset. This checkout was package/API-ready but lacked full downloaded kitchen
assets; a direct constructor succeeded while reset was blocked on fixture XML.

**Recovery**

Verify the complete asset prerequisite through `tasks-scenes-assets`, then verify
headless reset through `simulation-environments`. Keep package import, constructor,
reset, and full replay as distinct claims.

## Rendering or video writing fails

**Symptoms**

- Viewer/display initialization errors.
- EGL/GL context errors in offscreen mode.
- Unknown camera name or empty frame.
- Image/video codec writer failures.

**Recovery**

1. View existing dataset MP4s first; this avoids simulation.
2. Confirm selected camera names from the dataset/environment metadata.
3. Use one camera and `--n 1` for a bounded renderer probe; the playback CLI does not expose a `--first` flag.
4. Verify display requirements for `--render` or a supported headless backend for
   video writing.
5. Verify destination permissions, free space, and encoder support.

GPU visibility alone is not a rendering proof. Route backend configuration to
`simulation-environments`.

## Action playback diverges

**Symptoms**

- Playback warns that simulated states differ from recorded states.
- Open-loop trajectories drift or fail.

**Cause**

Action playback is sensitive to controller mode, package versions, model XML,
initial state, action ordering, and floating-point dynamics. Version 1.0.1 also
reorders LeRobot actions back to legacy control ordering using `modality.json`.

**Recovery**

Use recorded-state replay to inspect the trajectory. Verify exact RoboCasa,
MuJoCo, NumPy, and compatible robosuite versions; dataset controller metadata;
`modality.json`; and relative versus absolute action selection. Treat divergence
as evidence against deterministic action replay, not as a harmless video issue.

## Conversion would delete existing output

**Symptom**

A sibling `lerobot/` already exists beside the raw HDF5.

**Cause**

The maintained converter removes that directory before rebuilding it.

**Recovery**

Stop. Back up or move the existing output, or work in an isolated copy. Confirm
storage and renderer prerequisites, then convert a tiny fixture first. The
converter has no `--n`; use an intentionally small copied input if a bounded test
is required.

## State-to-observation extraction leaves temporary/output files

**Symptoms**

- `<dataset>_temp_<worker>.hdf5` files remain after worker failure.
- Output HDF5 is partial.
- Disk usage grows rapidly with camera images or many processes.

**Recovery**

Stop workers, preserve logs, and inspect each file before cleanup. Do not treat a
created output path as success. Retry with an explicit fresh output name,
`--n 1 --num_procs 1`, smaller images, and adequate free space. Configure GPU IDs
only after a renderer probe.

## Downloader fails or leaves partial extraction

**Possible surfaces**

- Network/Box link errors after retries.
- Permission or free-space failures.
- Archive extraction interruption.
- Existing destination conflict.

**Recovery**

Re-run the bundled planner to reconfirm exact selection and destination. Inspect
archive and extracted directories. Retry only the failed targeted dataset; avoid
`--all`. Use `--overwrite` only after deciding what to discard. The native
extractor uses archive extraction into the destination parent, so run it only on
trusted official download metadata and do not substitute arbitrary archives.

## Native tests are unavailable or misleading without data

`tests/test_datasets.py` expects legacy HDF5 and checks action bounds plus episode
object/layout/style metadata. `tests/test_dataset_playback.py` expects local
registered datasets, simulator assets, rendering/video output, and currently
contains a call shape that is inconsistent with the live playback function.
Neither is a no-data package smoke test.

With no full local datasets, defer these native candidates. Use registry probes,
CLI `--help`, bundled structural inspection, and a deliberately created tiny
fixture for bounded schema validation. Do not turn skipped data-dependent tests
into a dataset verification claim.
