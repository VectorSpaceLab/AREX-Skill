# Workflows

## 1) Download and normalize public trajectories

Self-contained generated-skill path, usable even before a RoboTwin source checkout exists. Run this from the generated skill root (`skills/disco/robotwin/`) or replace `scripts/robotwin_workspace.py` with its absolute path:

```bash
python scripts/robotwin_workspace.py download-data \
  --workspace /path/to/robotwin-workspace \
  adjust_bottle beat_block_hammer
```

Ready-workspace native path:

```bash
bash scripts/download_xpolicylab_data.sh
bash scripts/download_xpolicylab_data.sh adjust_bottle beat_block_hammer
HF_MAX_WORKERS=8 HF_EXTRACT_WORKERS=16 bash scripts/download_xpolicylab_data.sh
```

Side effects:
- downloads archive files from Hugging Face
- extracts them into a normalized RoboTwin layout
- creates `data/<task_config>/<task>/<embodiment>/data/`
- can keep or delete archives depending on `HF_KEEP_ARCHIVES`

Validation signals:
- `downloaded`, `extract`, and `done` messages appear for each task
- the target `data/` tree exists and contains numbered HDF5 episodes
- `scripts/validate_download_layout.py` reports no fatal issues

## 2) Collect fresh demonstrations

Self-contained generated-skill dispatcher:

```bash
python scripts/robotwin_workspace.py collect \
  --workspace /path/to/robotwin-workspace \
  --task-name <task_name> \
  --task-config <task_config> \
  --gpu-id <gpu_id>
```

Ready-workspace native path:

```bash
bash collect_data.sh <task_name> <task_config> <gpu_id>
# example: bash collect_data.sh beat_block_hammer demo_randomized 0
```

Side effects:
- sets `CUDA_VISIBLE_DEVICES`
- runs the task collection driver
- searches for working seeds, then replays them to save episodes
- writes normalized HDF5 episodes, videos, instructions, `scene_info.json`, and `seed.txt`
- clears per-episode caches after the merge step

Validation signals:
- the run prints a successful simulation count rather than repeated failure loops
- `data/<task_config>/<task>/<embodiment>/data/episode_0000000.hdf5` appears
- the paired `video/` and `instruction/` directories are populated

For simulator and asset bootstrap issues, switch to `simulation-core`.

## 3) Convert legacy raw episodes

```bash
python scripts/process_data_xpolicylab.py <task_name> <task_config> [episode_count] --overwrite
python scripts/process_data_xpolicylab.py --all --overwrite
```

Side effects:
- reads old raw episode folders from `data/<task>/<task_config>/data/`
- writes normalized XPolicyLab episodes under `data/<task_config>/<task>/<env_cfg_type>/data/`
- may copy `seed.txt` and `scene_info.json`
- writes `conversion_meta.json`

Validation signals:
- per-episode `[ok]` lines appear
- the output tree contains seven-digit `episode_*.hdf5` files
- `scripts/inspect_xpolicylab_hdf5.py` reports `format: xpolicylab`

## 4) Inspect or validate a tree

```bash
python scripts/inspect_xpolicylab_hdf5.py path/to/episode_0000000.hdf5
python scripts/validate_download_layout.py --root data/demo_clean
```

Side effects:
- read-only
- safe to run on user-provided paths
- useful for diagnosing partial downloads, numbering gaps, or schema drift

## 5) Hand off to downstream policy work

If the normalized dataset is ready for training or evaluation, hand it off to `policy-eval`.
That sub-skill owns policy-server setup, adapter checks, and rollout scheduling.
