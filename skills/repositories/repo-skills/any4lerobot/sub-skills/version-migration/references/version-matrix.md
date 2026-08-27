# Version matrix and environment gates

## Supported directions

| Source | Target | Evidence converter | Scope and primary risk |
|---|---|---|---|
| v1.6 (legacy v1.0–v1.6 family) | v2.0 | `convert_dataset_v16_to_v20.py` | Rebuilds metadata/data layout, assigns task indices, serializes stats, and may move Git-LFS videos and replace Hub folders. |
| v2.0 | v2.1 | `convert_dataset_v20_to_v21.py` plus episode-stats logic | Removes/recomputes episode stats, checks aggregate statistics, updates `codebase_version`, and optionally deletes the old aggregate stats file. |
| v2.1 | v2.0 | `convert_dataset_v21_to_v20.py` | Deletes/recreates aggregate stats, updates `codebase_version`, and optionally deletes episode stats. |
| v2.1 | v3.0 | `convert_dataset_v21_to_v30.py` | Consolidates data, video, task, episode, and statistics files; swaps directory trees and can delete old Hub paths. |
| v3.0 | v2.1 | `convert_dataset_v30_to_v21.py` | Splits consolidated parquet and videos back to per-episode files; uses `ffmpeg`; swaps roots and can download v3.0 from the Hub. |

There is **no v2.0→v1.6 or v2.0→v1.x converter** in the assigned source
evidence. Do not promise a reverse migration. There is also no direct v1.6↔v2.1
or v1.6↔v3.0 path: use documented intermediate versions and validate after
each hop.

## Version identity

Use all available evidence, not one string:

1. Read `codebase_version` from `meta/info.json` for v2.0/v2.1/v3.0.
2. For v1.6, inspect `meta_data/info.json`, `meta_data/stats.safetensors`,
   `data/`, and legacy video names. The v1.6 converter expects the legacy
   `meta_data` root and `stats.safetensors`.
3. Confirm path signatures and required files in
   [metadata-layouts](metadata-layouts.md).
4. If metadata and paths disagree, stop and make a repair/normalization plan;
   do not force a converter.

## Historical environment pins from the evidence

Run each migration in an isolated environment matched to the converter's
imports. Do not use the currently installed LeRobot package merely because it
imports.

| Route | Required LeRobot environment from the source README | Important dependencies/gates |
|---|---|---|
| v1.6→v2.0 | LeRobot v2.0 checkout at commit `c574eb49845d48f5aad532d823ef56aec1c0d0f2`, installed editable | `datasets`, `pyarrow`, `torch`, `safetensors`, `huggingface_hub`, video utilities, Git-LFS if videos are present. The script imports `lerobot.common.datasets.*` and robot config utilities. |
| v2.0→v2.1 | LeRobot v2.1 checkout at commit `d602e8169cbad9e93a4a3b3ee1dd8b332af7ebf8`, installed editable | `LeRobotDataset`, v2.1 conversion constants, stats computation, `numpy`, `tqdm`, process workers, and Hub API only for publication. |
| v2.1→v2.0 | The README pins the same v2.1 commit `d602e8169cbad9e93a4a3b3ee1dd8b332af7ebf8` for the supplied converter | It imports v2.1 dataset APIs and writes v2.0 metadata. Verify that the selected v2.1 environment still exposes both `STATS_PATH` and `EPISODES_STATS_PATH`. |
| v2.1→v3.0 | LeRobot v3.0 environment, as specified by the source README; use the exact v3.0 release/commit selected by the operator and record it | `jsonlines`, `pandas`, `pyarrow`, `datasets`, `huggingface_hub`, LeRobot v3 IO/video utilities, and a compatible `ffmpeg` stack for any video. |
| v3.0→v2.1 | The source README says to install LeRobot v3.0 before running this reverse utility, and to downgrade `datasets` to `<4.0.0` because `datasets>=4.0.0` introduces `List` and `Column` incompatibilities | `jsonlines`, `numpy`, `pyarrow`, `pandas`/datasets IO, `ffmpeg`, and v3 metadata utilities. Pin and record the exact working v3.0 package commit; do not assume the current API. |

The repository evidence contains mixed namespace generations: older routes use
`lerobot.common.datasets`, v2.x routes use `lerobot.datasets.lerobot_dataset`
and `lerobot.datasets.utils`, and v3 routes import from `lerobot.datasets`,
`lerobot.datasets.io_utils`, and `lerobot.datasets.video_utils`. In the current
LeRobot namespace, check for `lerobot.datasets.lerobot_dataset.LeRobotDataset`
and `LeRobotDatasetMetadata`; a passing import in one namespace does not prove
converter compatibility. The batch's inspected environment facts include
Python 3.11 and LeRobot 0.4.4, but that is not a historical migration pin.

## Root and publication semantics

- v2.0/v2.1 scripts accept `--root` as a local dataset root or otherwise load a
  cached/Hub dataset by `repo_id`; `--branch` controls the Hub revision when
  publishing. Keep `--push-to-hub` off during the first pass.
- v2.1→v3.0 uses `$HF_LEROBOT_HOME/<repo_id>` when `--root` is omitted. With a
  local `--root`, it must be the exact directory containing `meta/`, `data/`,
  and optionally `videos/`.
- v3.0→v2.1 likewise defaults to `$HF_LEROBOT_HOME/<repo_id>` and downloads a
  v3.0 revision if the root is absent. Prefer an explicit local root to avoid
  an implicit network read.
- v1.6→v2.0 uses `--local-dir` for staging/cache, but still uses `--repo-id`
  and Hub snapshot/download/upload logic. A `--test-branch` changes the
  destination branch; without it, the converter targets `main` and creates a
  v2.0 tag after upload.
- A repo id identifies a dataset, not a local path. Reject accidental values
  such as a non-existent local path passed as `repo_id`; resolve `--root` and
  `--local-dir` separately.
