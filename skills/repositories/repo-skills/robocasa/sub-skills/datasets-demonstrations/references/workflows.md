# Dataset workflows

All acquisition, playback, and conversion commands below are opt-in. Begin with
registry-only and filesystem-only checks; do not let a convenience demo trigger an
unexpected download or renderer.

## 1. Registry metadata to a verified local dataset

### Step 1: plan without networking

For one task:

```bash
python scripts/plan_dataset_download.py \
  --tasks CloseBlenderLid \
  --split target \
  --source human \
  --require-local
```

For a task set/soup query:

```bash
python scripts/plan_dataset_download.py --list-task-sets --list-soups
python scripts/plan_dataset_download.py \
  --task-set atomic_seen --split target --source human
```

The planner imports the installed registry, reports every resolved path and its
`local_exists` state, and prints package downloader commands. It does not execute
commands, contact a host, create directories, or modify macro files. Exit 2 with
`--require-local` means the metadata exists but at least one local path does not.

For a custom dataset root, use a process-local check:

```bash
python scripts/plan_dataset_download.py \
  --dataset-base-path /data/robocasa \
  --tasks CloseBlenderLid --split target --source human
```

The native downloader runs in another process, so configure its
`DATASET_BASE_PATH` consistently; the planner's temporary override is not
inherited.

### Step 2: approve acquisition explicitly

The native CLI choices are `human` and `mimicgen`; its split choices are
`pretrain` and `target`. A targeted dry-run is:

```bash
python -m robocasa.scripts.download_datasets \
  --tasks CloseBlenderLid \
  --split target \
  --source human \
  --dryrun
```

The package prompts even in dry-run mode. Confirming a dry run prints intended
locations but does not download. Only after reviewing destination, available
storage, network policy, and existing directories should the user remove
`--dryrun`:

```bash
python -m robocasa.scripts.download_datasets \
  --tasks CloseBlenderLid \
  --split target \
  --source human
```

Safety rules:

- Avoid `--all` until aggregate multi-GB storage and time have been approved.
- Add `--overwrite` only after backing up or deliberately discarding the selected
  existing datasets.
- Treat each archive download/extraction as a state-changing operation. If it is
  interrupted, inspect the destination rather than assuming completion.
- Use `mimicgen` only at the download CLI boundary. Use `mg` for direct registry
  calls.
- Dataset downloads and kitchen-asset downloads are independent prerequisites.

### Step 3: inspect local structure

```bash
python scripts/inspect_dataset.py --dataset /data/robocasa/v1.0/.../lerobot
```

The command returns nonzero for missing paths and for trees that exist but lack
trajectory data. It reports separate training/sample, video, and simulator-replay
readiness. It does not instantiate RoboCasa or render.

Optionally load exactly one local LeRobot sample with networking forced off:

```bash
python scripts/inspect_dataset.py \
  --dataset /data/robocasa/v1.0/.../lerobot \
  --sample-index 0
```

Use the installed native statistics CLI only after the tree passes:

```bash
python -m robocasa.scripts.dataset_scripts.get_dataset_info \
  --dataset /data/robocasa/v1.0/.../lerobot
```

Despite a stale internal help/docstring saying “hdf5”, this CLI constructs a
`LeRobotDataset` and expects the LeRobot root. `--verbose` prints each episode's
first-sample structure; `--all_stats` traverses episode metadata and can be much
slower. The command checks aggregate action bounds against `[-1, 1]`.

## 2. Select and validate a dataset soup

Use the actual `task_set` keyword:

```python
from pathlib import Path
from robocasa.utils.dataset_registry import get_ds_soup

soup = get_ds_soup(
    split="target",
    task_set="atomic_seen",
    source="human",
    demo_fraction=0.1,
)

ready, missing = [], []
for entry in soup:
    (ready if Path(entry["path"]).is_dir() else missing).append(entry)
if missing:
    names = [entry["task"] for entry in missing]
    raise FileNotFoundError(f"registered but not downloaded: {names}")
```

Then decide three independent policies:

1. **Subset policy:** apply each metadata `filter_key`; direct LeRobot construction
   does not apply it.
2. **Weight policy:** assign explicit per-dataset weights or preserve verified
   `ds_weight` values from a prebuilt co-training soup.
3. **Failure policy:** normally fail before training if any required path is
   absent. Silently dropping missing datasets changes the experimental mixture.

Record the selected soup name/task set, source, split, filter keys, and normalized
weights with experiment configuration. `source="all"` can yield two entries for a
task (human plus `mg`); it does not fuse them.

## 3. Random sample access

After local inspection, use `LeRobotDataset` as shown in
[data formats](data-formats.md#local-random-sample-access-with-lerobot-033).
Prefer a seeded `random.Random(seed)` for reproducible inspection. Check
`meta/info.json` before hard-coding image or annotation keys. If only trajectory
numbers/actions are needed, video files may be avoidable; image sample access
requires the corresponding camera MP4 and decoder backend.

## 4. Playback selection

### Lowest-risk: view recorded videos

Open an existing camera MP4 under `videos/`. This does not reconstruct the
simulator and does not require `model.xml.gz` or `states.npz`.

### LeRobot simulator replay

Preflight:

```bash
python scripts/inspect_dataset.py --dataset /data/run/lerobot
python -m robocasa.scripts.dataset_scripts.playback_dataset --help
```

Bounded state replay to a video:

```bash
python -m robocasa.scripts.dataset_scripts.playback_dataset \
  --dataset /data/run/lerobot \
  --n 1 \
  --video_path /data/run/replay.mp4 \
  --render_image_names robot0_agentview_left robot0_eye_in_hand
```

Omitting `--render` requests offscreen video writing. Adding `--render` requests
an interactive on-screen viewer and supports one camera only. `--use-actions`
changes from recorded-state replay to relative open-loop action playback and may
diverge. Do not use LeRobot `--use-obs`, `--filter_key`, or
`--use-abs-actions` in 1.0.1.

Simulator replay requires the full replay extras, compatible task/controller
code, referenced kitchen/object assets, and a working renderer. A model XML file
inside the dataset does not guarantee that every referenced asset exists.

### Legacy HDF5 playback

Static inspection:

```bash
python scripts/inspect_dataset.py --dataset /data/run/demo.hdf5
```

Offline image playback is preferred when embedded observations exist:

```bash
python -m robocasa.scripts.dataset_scripts.playback_dataset_hdf5 \
  --dataset /data/run/demo.hdf5 \
  --n 1 --use-obs \
  --render_image_names robot0_agentview_left robot0_eye_in_hand \
  --video_path /data/run/observations.mp4
```

This route cannot combine `--use-obs` with action flags. For simulator state
replay, remove `--use-obs`. Use `--use-actions` only for the relative `actions`
array; use `--use-abs-actions` only after verifying `actions_abs` exists and the
controller metadata matches. HDF5 `--filter_key <name>` requires
`mask/<name>`.

## 5. HDF5 conversion

Before conversion:

1. Inspect HDF5 and verify `env_args`, per-episode states, actions, model XML, and
   episode metadata.
2. Back up or remove ambiguity around the sibling `lerobot/`; the converter
   deletes an existing one.
3. Verify kitchen assets and a one-environment reset through
   `simulation-environments`.
4. Verify the intended renderer/cameras and video encoder.
5. Estimate output size for three video streams plus Parquet/extras.
6. Work on a copy or tiny fixture first because the converter has no episode-limit
   flag.

Then run:

```bash
python -m robocasa.scripts.dataset_scripts.convert_hdf5_lerobot \
  --raw_dataset_path /data/run/demo.hdf5 \
  --camera_names robot0_eye_in_hand robot0_agentview_left robot0_agentview_right \
  --camera_height 256 --camera_width 256
```

Afterward, run the bundled inspector and native info command on the generated
`lerobot/`, then inspect one sample and one recorded MP4. Simulator playback is a
separate, stronger check.

For state-to-observation HDF5 extraction, use the advanced command and preflight
in [data formats](data-formats.md#state-to-observation-hdf5-extraction). Keep
`--n 1 --num_procs 1` for the first run, choose an explicit new output name, and
only scale workers/rendering after validating one episode.

## 6. Dataset-backed environment setup

A registry record contributes only configuration values:

```python
task = meta["task"]
split = meta["split"]
horizon = meta["horizon"]
```

Pass the task/split into the verified environment workflow and use `horizon` as
the 1.0.1 evaluation limit. Do not pass the dataset path to an environment
constructor unless that API explicitly consumes it. For episode replay, use
`dataset_meta.json`, `ep_meta.json`, `model.xml.gz`, and `states.npz` through the
maintained playback path rather than reconstructing their reset logic ad hoc.

Package/API readiness was established during inspection, and direct environment
construction succeeded, but reset was blocked without downloaded fixture XML.
Therefore a registry query or constructor success is not evidence of a complete
simulation run. Route environment details to `simulation-environments` and asset
resolution to `tasks-scenes-assets`.

## 7. Convenience demo caution

`python -m robocasa.demos.demo_tasks` combines task selection, missing-dataset
download, and interactive/offscreen playback. When the selected dataset is
absent, it calls the downloader programmatically. Prefer the explicit plan,
download, inspect, and playback stages above so network and rendering side effects
remain visible.

Live teleoperation and new human demonstration capture are outside this
sub-skill. Route them to `teleoperation-and-collection`; return here only to
inspect or convert the captured HDF5.
