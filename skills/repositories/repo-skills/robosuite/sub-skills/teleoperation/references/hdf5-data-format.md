# HDF5 data format

This reference describes the teleop demo files produced by robosuite data-collection flows and the raw per-episode logs that feed them.

## 1. Raw per-episode logs from `DataCollectionWrapper`

Before aggregation, each interaction episode is stored as a folder containing:

```text
ep_<timestamp>/
  model.xml
  ep_meta.json
  state_<timestamp>.npz
```

The `state_*.npz` chunks contain:
- `states`: stacked flattened MuJoCo states
- `action_infos`: one entry per sampled step; each entry always includes `actions` and may include `actions_abs`
- `successful`: boolean success flag
- `env`: environment class name

Important behavior:
- The wrapper records the simulator state after the first interaction, not during reset-only churn.
- Successful episodes are flushed and then aggregated into HDF5.
- If you need the raw `actions_abs` values, keep the per-episode NPZ logs; the final HDF5 aggregation stores only `actions`.

## 2. Assembled `demo.hdf5`

The aggregated demo file has the following structure:

```text
data (group)
  attrs:
    date
    time
    repository_version
    env
    env_info
  demo_1 (group)
    attrs:
      model_file
    states (dataset)
    actions (dataset)
  demo_2 (group)
    ...
```

### Root `data` attributes

| Attribute | Meaning |
| --- | --- |
| `date` | Collection date |
| `time` | Collection time |
| `repository_version` | robosuite version used during collection |
| `env` | Environment name |
| `env_info` | JSON-encoded environment / robot / controller config |

### Demo-group attributes and datasets

| Item | Meaning |
| --- | --- |
| `model_file` | Episode MJCF metadata; in the collection path this is stored inline as XML text |
| `states` | Flattened MuJoCo states ordered by time |
| `actions` | Environment actions ordered by time |

Shape rules:
- `states.shape[0]` is the episode length in steps.
- `actions.shape[0]` should match `states.shape[0]` after aggregation.
- The final state from the raw logs is trimmed during aggregation so the actions and states stay aligned.

## 3. `model_file` layout note

The human-demo collection path stores the episode XML inline in `model_file`. Some state-sampling workflows expect a companion `models/` folder and treat `model_file` as a filename instead.

That means:
- `demo.hdf5` created from human-demo aggregation is enough for summary and playback.
- `DemoSamplerWrapper(need_xml=True)` may require a dataset layout that includes `models/` files.
- The bundled inspection helper reports whether `model_file` looks like inline XML or a filename-style reference.

## 4. Playback semantics

Two playback strategies exist:

1. **State playback**
   - Load each stored state with `set_state_from_flattened`.
   - This is the exact reproduction path.

2. **Action playback**
   - Step the simulator with recorded actions.
   - This is open loop and may drift even when the same seed or controller config is used.

Same-machine warning:
- Deterministic action playback has been verified only on the same machine that collected the demo.
- Cross-platform or cross-machine playback can diverge even when the environment names match.
- If you need exact reproduction, use state playback rather than action playback.

## 5. Quick inspection pattern

```python
import h5py

with h5py.File("demo.hdf5", "r") as f:
    data = f["data"]
    print(dict(data.attrs))
    for demo_name in data:
        demo = data[demo_name]
        print(demo_name, demo["states"].shape, demo["actions"].shape)
```

Use the bundled `inspect_demo_hdf5.py` script when you want the same checks wrapped in a safe CLI.
