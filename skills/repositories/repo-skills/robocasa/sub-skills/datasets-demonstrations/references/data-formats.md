# RoboCasa dataset formats

Identify the format before loading data or selecting playback flags. The current
public datasets use LeRobot; legacy/raw demonstration workflows use HDF5.

## LeRobot tree used by RoboCasa 1.0.1

```text
lerobot/
├── meta/
│   ├── info.json
│   ├── tasks.jsonl
│   ├── episodes.jsonl
│   ├── episodes_stats.jsonl
│   ├── stats.json
│   ├── modality.json
│   └── embodiment.json
├── data/
│   └── chunk-<chunk_id>/episode_<episode_id>.parquet
├── videos/
│   └── chunk-<chunk_id>/
│       └── observation.images.<camera>/episode_<episode_id>.mp4
└── extras/
    ├── dataset_meta.json
    └── episode_<episode_id>/
        ├── ep_meta.json
        ├── model.xml.gz
        └── states.npz
```

### Standard training material

- `meta/info.json`: robot type, frames, episodes, fps, feature definitions, and
  path/chunking templates consumed by LeRobot.
- `meta/tasks.jsonl`: task/language records and task indices.
- `meta/episodes.jsonl`: episode indices, language/task association, and lengths.
- `meta/episodes_stats.jsonl` and `meta/stats.json`: episode and aggregate feature
  statistics.
- `meta/modality.json`: named slices of state and action vectors used by RoboCasa
  and selected policy loaders.
- `meta/embodiment.json`: embodiment description.
- `data/.../*.parquet`: low-dimensional observations, actions, rewards/dones,
  timestamps, indices, and annotations according to `info.json`.
- `videos/.../*.mp4`: one stream per camera feature and episode. Public RoboCasa
  examples use left and right agent views plus the eye-in-hand view.

### RoboCasa replay extras

The `extras/` subtree is non-standard LeRobot metadata retained for simulator
reconstruction:

- `dataset_meta.json` stores dataset-level environment arguments and controller
  configuration copied from the source HDF5 metadata.
- `ep_meta.json` stores layout/style, fixtures, objects, and the concrete episode
  language context. Playback resolves object placeholders from this data when
  possible.
- `model.xml.gz` stores the episode's compressed MuJoCo model XML.
- `states.npz` stores raw flattened MuJoCo states under the `states` key. It is
  for replay and observation regeneration, not ordinary policy training.

These support different readiness claims:

| Local material | Supported claim |
|---|---|
| `meta/` only | Metadata may be inspectable; no sample/data claim |
| `meta/` + Parquet | Low-dimensional sample access may be ready |
| Above + camera MP4 | Video-backed image sample access may be ready |
| Above + complete `extras/` | Replay inputs are present, but simulator assets/rendering still require validation |

A registry target may exist even when every one of these files is absent.

## Local random sample access with LeRobot 0.3.3

Check the path first so LeRobot is never used as an accidental network fallback:

```python
from pathlib import Path
import random
from lerobot.datasets.lerobot_dataset import LeRobotDataset

root = Path(meta["path"])
required = [root / "meta" / "info.json", root / "data"]
if not all(path.exists() for path in required):
    raise FileNotFoundError(f"incomplete local LeRobot dataset: {root}")

dataset = LeRobotDataset(repo_id="robocasa365", root=root)
episode_index = random.choice(list(dataset.meta.episodes))
start = int(dataset.episode_data_index["from"][episode_index])
end = int(dataset.episode_data_index["to"][episode_index])
if end <= start:
    raise ValueError(f"empty episode {episode_index}")
sample = dataset[random.randrange(start, end)]

right_image = sample["observation.images.robot0_agentview_right"]
action = sample["action"]
instruction = sample["task"]
```

`repo_id` is required by the 0.3.3 constructor even when `root` is local; it does
not identify a RoboCasa task. Use the dataset's actual feature names from
`meta/info.json`, because camera or annotation keys can differ across variants.
The bundled inspector's optional `--sample-index` forces Hugging Face offline mode
and reports shapes/dtypes instead of printing tensors or images.

`demo_fraction` and `filter_key` from registry metadata are not automatically
applied by this constructor. Select episode/sample indices explicitly or use a
verified loader that honors the filter.

## Legacy/raw HDF5

The maintained legacy playback and conversion tools expect a robomimic-style
structure similar to:

```text
demo.hdf5
├── data/                              # attrs include env_args and total
│   ├── demo_0/                        # attrs include model_file, ep_meta, num_samples
│   │   ├── actions
│   │   ├── actions_abs                # optional
│   │   ├── states
│   │   ├── rewards                    # optional/raw-stage dependent
│   │   ├── dones                      # optional/raw-stage dependent
│   │   ├── obs/<observation-key>      # optional until extracted
│   │   └── next_obs/<observation-key> # optional
│   └── demo_1/...
└── mask/<filter-key>                  # optional arrays of episode names
```

Important contracts:

- `data.attrs["env_args"]` must be JSON environment metadata for simulator-based
  playback/conversion.
- Each replayed episode needs `states`; state/action replay also needs
  `model_file`, and task-aware output normally needs `ep_meta`.
- `actions` uses the legacy 12-dimensional ordering: end-effector position,
  end-effector rotation, gripper close, base motion, then control mode.
- `actions_abs` is optional and only meaningful when it was actually recorded.
- Offline observation playback needs image datasets named
  `obs/<camera>_image` for every selected camera.
- Filter masks contain encoded episode names and are supported by the HDF5
  playback tool.

Do not rename `demo_<integer>` groups casually: native tools sort by the numeric
suffix and preserve names to keep filter masks consistent.

## Playback command/flag matrix

Use package-module entry points so commands do not depend on a repository
checkout:

```bash
python -m robocasa.scripts.dataset_scripts.playback_dataset --help
python -m robocasa.scripts.dataset_scripts.playback_dataset_hdf5 --help
```

| Capability | LeRobot `playback_dataset` | Legacy `playback_dataset_hdf5` |
|---|---|---|
| Input | local LeRobot root | `.hdf5` file or directory containing `demo.hdf5` |
| Default | simulator state replay | simulator state replay |
| `--n N` | first `N` sorted extra episodes | random `N` episode groups |
| `--use-actions` | relative open-loop actions reconstructed from Parquet | `actions` open-loop |
| `--use-abs-actions` | not implemented as a usable LeRobot path; do not use | uses `actions_abs` if present |
| `--use-obs` | rejected by current implementation | offline image-observation video; cannot combine with action flags |
| `--filter_key` | rejected by current implementation | supported when `mask/<key>` exists |
| `--render` | on-screen; exactly one camera | on-screen; exactly one camera |
| no `--render` | writes video, default 20 fps | writes video, default 20 fps |
| replay extras | required | embedded in HDF5 attrs/datasets |

`--use-actions` and `--use-abs-actions` are mutually exclusive. Do not pass HDF5
flags merely because a LeRobot registry record has a `filter_key`. First run the
bundled inspector and select the matching command.

Recorded MP4 files under `videos/` can also be viewed directly without simulator
replay. That is the lowest-risk visualization path when rendering or assets are
unavailable.

## HDF5-to-LeRobot conversion output

The conversion command is:

```bash
python -m robocasa.scripts.dataset_scripts.convert_hdf5_lerobot \
  --raw_dataset_path /data/run/demo.hdf5 \
  --camera_height 256 --camera_width 256
```

It writes `/data/run/lerobot/`, including:

- 20 fps H.264/yuv420p camera videos;
- Parquet episode data;
- 16-dimensional state and 12-dimensional action arrays reordered according to
  the bundled PandaOmron modality definition;
- language/task indices, reward, and done features;
- aggregate statistics, modality, and embodiment metadata;
- `extras/` replay metadata copied from HDF5.

**Destructive behavior:** if the sibling `lerobot/` exists, the converter removes
it before conversion. Back it up or choose an isolated working copy first. The
converter reconstructs every episode environment and renders three cameras by
default, so model XML, assets, controller metadata, video encoding support,
storage, and rendering must all be ready. Start with a copied tiny fixture or a
bounded source dataset; the converter itself has no `--n` flag.

## State-to-observation HDF5 extraction

`dataset_states_to_obs` is a separate advanced rewrite path:

```bash
python -m robocasa.scripts.dataset_scripts.dataset_states_to_obs \
  --dataset /data/run/demo.hdf5 \
  --output_name demo_im128.hdf5 \
  --n 1 --num_procs 1 --done_mode 2
```

It creates an output HDF5 beside the input, reconstructs environments, optionally
renders images, creates temporary per-process files, merges episodes, and adds
standard dataset-size masks. It can allocate worker processes to GPU IDs, but GPU
flags do not prove that a compatible rendering backend exists. Use one process
and one demo first, provide an explicit output name, and verify free disk space.
Do not combine this expensive rewrite with LeRobot playback flags.
