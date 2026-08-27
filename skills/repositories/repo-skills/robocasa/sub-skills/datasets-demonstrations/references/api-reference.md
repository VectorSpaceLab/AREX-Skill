# Dataset registry API reference

This reference describes the live RoboCasa 1.0.1 API. It corrects documentation
examples where names or source aliases no longer match the implementation.

## Compatibility baseline

The inspected package combination was:

| Package | Verified version / constraint |
|---|---|
| RoboCasa | 1.0.1 |
| robosuite | 1.5.2; RoboCasa accepts public `robosuite>=1.5.2` |
| MuJoCo | exactly 3.3.1 |
| NumPy | exactly 2.2.5 |
| Gymnasium | 0.29.1 |
| h5py | 3.16.0 |
| LeRobot | 0.3.3 |

RoboCasa import performs the exact MuJoCo and NumPy checks and the robosuite
minimum-version check. MimicGen is optional and was not installed in the inspected
environment. Import inspection registered 374 kitchen environments, but that
only establishes registry/package readiness.

## Published dataset families

The RoboCasa 1.0.1 documentation reports more than 2,200 hours across these main
families:

| Split/source | Tasks | Kitchens/scenes | Demos per task | Reported hours |
|---|---:|---:|---:|---:|
| Pretraining human | 300 (65 atomic, 235 composite) | 2,500 pretraining kitchens | 100 | 482 |
| Pretraining MimicGen | 60 atomic | 2,500 pretraining kitchens | about 10,000 | 1,615 |
| Target human | 50 | 10 held-out target kitchens | 500 | 193 |

The target tasks are grouped as 18 atomic-seen, 16 composite-seen, and 16
composite-unseen. Target composite episodes additionally carry per-frame subtask
annotations (subtask index, atomic skill, pick/place/navigate stage, and natural
language) for hierarchical learning. These are published corpus statistics, not
proof that any local path contains the complete corpus. Inspect local metadata,
frame/episode counts, and annotations before making experiment-specific claims.

## Exact functions

Import the public functions from either `robocasa.utils.dataset_registry` (which
re-exports them) or `robocasa.utils.dataset_registry_utils`.

```python
get_ds_meta(task, split, source="human", demo_fraction=1.0)
get_ds_soup(split, task_set, source, demo_fraction=1.0)
```

A related convenience function is:

```python
get_ds_path(task, source, split="pretrain", return_info=False)
```

### `get_ds_meta`

```python
from pathlib import Path
from robocasa.utils.dataset_registry import get_ds_meta

meta = get_ds_meta(
    task="CloseBlenderLid",
    split="target",
    source="human",
    demo_fraction=1.0,
)
if meta is None:
    raise LookupError("that task/split/source has no registered dataset")
if not Path(meta["path"]).is_dir():
    raise FileNotFoundError(
        "registry metadata exists, but the opt-in dataset is not present locally"
    )
```

The returned mapping contains:

| Key | Meaning |
|---|---|
| `path` | Expected local LeRobot root, ending in `lerobot` (or `lerobot_cotraining_cams`) |
| `horizon` | Task horizon from the 1.0.1 registry |
| `filter_key` | Requested demonstration count encoded as `<N>_demos` |
| `task` | Exact task class/registry name |
| `split` | `pretrain`, `target`, or `real` |
| `source` | Normalized registry token used in the call |
| `url` | Present only if that registry entry carries a download link |

Main source semantics:

- `human`: teleoperated demonstrations. The registry assumes 100 demos for a
  pretraining task and 500 for a target task. Real-data assumptions are 30 demos
  for atomic and 50 for composite tasks.
- `mg`: provided MimicGen demonstrations. Most entries assume 10,000 demos;
  `OpenCabinet` assumes 5,000.
- `human_cotraining_cams`, `mg_5x5`, and `mg_5x1`: specialized registered
  variants used by selected experiments.

`get_ds_meta` does **not** accept `source="mimicgen"`; use `source="mg"`.
`get_ds_path` does accept `mimicgen` as an alias, and the download CLI maps its
public `mimicgen` choice to `mg` internally. Do not transfer an alias from one API
to another without checking the signature.

If a task exists but the requested split/source has no path, `get_ds_meta`
returns `None`. An unknown task raises `ValueError`. Invalid splits or unsupported
sources fail validation. Validate `0 < demo_fraction <= 1` before calling: the
function computes an integer filter count but does not enforce a safe range.

### `demo_fraction` is metadata, not a physical slice

For a target human dataset, `demo_fraction=0.1` yields `filter_key="50_demos"`;
for a pretraining human dataset it yields `"10_demos"`. The resolved path is
unchanged. Directly constructing `LeRobotDataset(root=meta["path"], ...)` therefore
loads the local dataset; it does not automatically apply the registry filter key.
A training loader must explicitly honor `filter_key`, or the caller must select
indices. The LeRobot playback CLI rejects `--filter_key`.

### Horizon update in 1.0.1

RoboCasa 1.0.1 increased task horizons by 1.5x for consistency. Use
`meta["horizon"]` from the installed 1.0.1 registry for evaluation rather than
copying older values from a paper, configuration, or downloaded metadata.

## Path resolution and `DATASET_BASE_PATH`

Each registry entry stores a relative folder such as
`v1.0/<split>/<task-kind>/<TaskName>/<date>`. `get_ds_meta` resolves it as follows:

1. If `robocasa.macros.DATASET_BASE_PATH` is `None`, use the installed RoboCasa
   project/package parent followed by `datasets/`.
2. Otherwise, use `DATASET_BASE_PATH` as the dataset root.
3. Append the registered folder and then `lerobot` (or the co-training camera
   directory name).

A custom base should therefore contain the versioned `v1.0/` subtree; do not set
it to the `v1.0/` directory itself. For a process-local, non-mutating override,
set the macro before importing the registry:

```python
import robocasa.macros as macros
macros.DATASET_BASE_PATH = "/data/robocasa"

from robocasa.utils.dataset_registry import get_ds_meta
```

For persistent configuration, apply the root skill's macro/configuration guidance.
The bundled planner offers `--dataset-base-path` only as a process-local planning
override; a later downloader process must be configured consistently.

## Task sets and dataset soups

The live soup signature uses `task_set`, **not** the stale documentation keyword
`task_soup`:

```python
from robocasa.utils.dataset_registry import get_ds_soup

entries = get_ds_soup(
    split="target",
    task_set="atomic_seen",
    source="human",
    demo_fraction=1.0,
)
```

Calling with `task_soup=` raises `TypeError: unexpected keyword argument
'task_soup'`.

The inspected registry exposed 16 task sets:

- broad: `all_tasks`, `all_atomic_tasks`, `all_composite_tasks`;
- pretraining: `pretrain50`, `pretrain100`, `pretrain200`, `pretrain300`;
- target: `atomic_seen`, `composite_seen`, `composite_unseen`, `target50`;
- synthetic: `mg_dataset_tasks` (60 tasks with registered MimicGen data);
- lifelong: `lifelong_learning_phase1` through `lifelong_learning_phase4`.

`get_ds_soup` accepts source tokens `human`, `human_cotraining_cams`, `mg`,
`mg_5x5`, `mg_5x1`, and `all`. `all` concatenates available human and `mg`
metadata per task; it does not merge files or verify paths. The inspected
`target/atomic_seen/human` query returned 18 metadata entries.

`DATASET_SOUP_REGISTRY` exposes 28 prebuilt lists, including:

- `target50`, target seen/unseen groups, and their `10p`/`30p` variants;
- `pretrain_human50`, `pretrain_human100`, `pretrain_human300`;
- human-plus-MimicGen mixtures such as `pretrain_human100_mg60`;
- `pretrain_atomic60_human` and `pretrain_atomic60_mg`;
- four lifelong-learning phase soups;
- environment-diversity variants and real/simulation co-training soups.

Always copy a prebuilt soup before mutating it because the registry stores shared
list/dict objects:

```python
from copy import deepcopy
from robocasa.utils.dataset_registry import DATASET_SOUP_REGISTRY

soup = deepcopy(DATASET_SOUP_REGISTRY["target_atomic_seen"])
missing = [entry["path"] for entry in soup if not Path(entry["path"]).is_dir()]
```

## Soup weights

A soup is a list of per-dataset metadata records, not a concatenated dataset.
Training code instantiates each local dataset and then supplies mixture weights.
Most simulated soups do not carry `ds_weight`; choose and record weights explicitly.
Real-data co-training soups use `add_cotraining_weights` to assign relative
weights across real, matching digital-cousin, and other simulation groups.
That helper normalizes by the first resulting weight, so values are relative, not
probabilities summing to one.

The documented `LeRobotMixtureDataset` / `LeRobotSingleDataset` route belongs to
an optional GR00T integration. Do not claim it is available merely because the
core registry imports. For framework-independent work, preserve the same concept:
validate every path, construct one dataset per record, honor each filter, and pass
explicit weights to the chosen sampler.

## `lerobot_utils` replay and ordering helpers

The maintained `robocasa.utils.lerobot_utils` module owns the RoboCasa-specific
bridge between LeRobot files and simulator replay. The useful read-only helpers
are:

```python
get_env_metadata(dataset_dir)
get_modality_dict(dataset_dir)
get_episodes(dataset_dir)
get_episode_states(dataset_dir, ep_num)
get_episode_model_xml(dataset_dir, ep_num)
get_episode_meta(dataset_dir, ep_num)
get_episode_actions(dataset_dir, ep_num, abs_actions=False)
```

They read `extras/dataset_meta.json`, `meta/modality.json`, and numbered extras
files; they do not download missing files. `get_episode_actions` reads one
`data/*/episode_<ep_num>.parquet` and reorders the LeRobot action vector back to
legacy control order. `abs_actions=True` currently raises `NotImplementedError`.

The live action slice map is:

| Legacy/control key | HDF5 slice | LeRobot modality slice |
|---|---:|---:|
| `end_effector_position` | `0:3` | from `modality.json` |
| `end_effector_rotation` | `3:6` | from `modality.json` |
| `gripper_close` | `6:7` | from `modality.json` |
| `base_motion` | `7:11` | from `modality.json` |
| `control_mode` | `11:12` | from `modality.json` |

State conversion uses these HDF5 keys: `robot0_base_pos`,
`robot0_base_quat`, `robot0_base_to_eef_pos`, `robot0_base_to_eef_quat`, and
`robot0_gripper_qpos`, mapped respectively to base position, base rotation,
relative end-effector position, relative end-effector rotation, and gripper
qpos modality fields. Do not hard-code destination offsets; read
`modality.json`.

`playback_utils.resolve_instruction_from_ep_meta` returns `ep_meta["lang"]` and,
when it contains placeholders, substitutes values from `object_cfgs` using the
object name and `<name>_lang`. It leaves unresolved placeholders intact. This is
why replay should preserve `ep_meta.json`, rather than retaining only a language
integer from `tasks.jsonl`.

## Dataset-backed environments

Registry metadata can provide `task`, `split`, and the updated `horizon` for an
environment configuration. It does not provide a ready simulator by itself.
Before reset or replay, independently verify:

- the task is registered by the installed RoboCasa version;
- required kitchen fixture/object assets exist;
- the dataset has replay extras (`dataset_meta.json`, per-episode model XML,
  episode metadata, and raw states);
- the selected rendering backend and cameras are available.

Route environment construction/reset/action semantics to
`simulation-environments`; route task/scene/asset choices to
`tasks-scenes-assets`.
