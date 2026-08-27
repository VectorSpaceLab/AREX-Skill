# Configuration contract

## Loading and inheritance

`src/utils/io_utils.py:load_config` loads YAML with `yaml.full_load`, follows
`inherit_from` recursively, and deep-merges child mappings over the base. A
scene config normally contains only `inherit_from`, `data`, and occasional
`cam` overrides:

```yaml
inherit_from: configs/Replica/replica.yaml
data:
  scene_name: office0
  input_path: data/Replica-SLAM/Replica/office0/
  output_path: output/Replica/office0/
```

For portable tooling, resolve a relative `inherit_from` first against the file
that declares it. The repository's checked-in examples also contain
repo-root-relative values such as `configs/Replica/replica.yaml`; when running
from the repository root, the bundled validator accepts that legacy form as a
fallback and reports it. Absolute inheritance paths are accepted for local
experiments but should not be committed to a public skill or shared config.
Reject missing bases, malformed YAML, non-mapping documents, and inheritance
cycles before a GPU run.

The source loader leaves `data.input_path` and `data.output_path` as written;
they are interpreted relative to the process working directory by downstream
code. Keep paths relative to a documented working root, or pass explicit CLI
overrides. The validator reports relative paths and can check their existence
with `--path-base`.

## Required effective shape

After inheritance, require these keys:

```yaml
project_name: <string>
dataset_name: replica | tum_rgbd | scan_net | scannetpp
checkpoint_path: <string or null>
use_wandb: <boolean>
frame_limit: -1                 # or a non-negative integer
seed: <integer>
mapping: <mapping>
tracking: <mapping>
cam:
  H: <positive integer>
  W: <positive integer>
  fx: <positive number>
  fy: <positive number>
  cx: <number>
  cy: <number>
  depth_scale: <positive number>
data:
  scene_name: <non-empty string>
  input_path: <path>
  output_path: <path>
  # optional loader-level override:
  frame_limit: <integer >= -1>
```

The validator checks that `mapping` and `tracking` are mappings even though
this sub-skill does not prescribe their optimization values. It does not
attempt to validate optimizer semantics. `checkpoint_path: null` is the
normal fresh-run value.

Dataset-specific keys:

| `dataset_name` | Required or conditional keys |
|---|---|
| `replica` | Replica camera values; `data` scene path must contain `results/` and `traj.txt` when data checking is enabled. |
| `tum_rgbd` | `cam.crop_edge` and `cam.distortion` are strongly recommended for the supplied scenes; a scene must have `rgb.txt`, `depth.txt`, and `groundtruth.txt` or `pose.txt`. |
| `scan_net` | ScanNet camera values; scene must have `color/`, `depth/`, and `pose/`. |
| `scannetpp` | `data.use_train_split` must be a boolean; `cam` must provide per-scene dimensions and intrinsics, plus `depth_scale`; DSLR split and camera metadata must agree. |

`crop_edge` defaults to zero in the dataset class. `distortion` is optional and
is passed to OpenCV when present; supply four or five numeric coefficients in
the convention expected by that OpenCV installation. Do not copy TUM
coefficients into a different scene without checking its calibration.

The top-level `frame_limit` is part of the run configuration. When constructing
a dataset, `GaussianSLAM` merges `data` and `cam` and passes that mapping to the
dataset class, so a `data.frame_limit` value is the effective loader limit when
present. The supplied ScanNet++ scene configs put `frame_limit: 250` under
`data`; do not assume a top-level value overrides it. Check the effective
location before launch.

## Supplied config families

Use the default files as templates, not as guarantees that data is installed:

- `configs/Replica/replica.yaml` plus `office*.yaml` or `room*.yaml`;
- `configs/TUM_RGBD/tum_rgbd.yaml` plus one per-sequence calibration file;
- `configs/ScanNet/scannet.yaml` plus a numeric scene override;
- `configs/scannetpp/scannetpp.yaml` plus a scene ID override.

Scene overrides may replace only selected camera fields. For example, ScanNet
scene `0169_00` and `0181_00` override focal lengths and principal points while
inheriting dimensions, depth scale, and crop. Validate the merged result rather
than judging a scene file in isolation.

## Path and override checklist

Before launch, record:

- the current working directory or an explicit `--path-base` used to resolve
  relative paths;
- the effective config path and every resolved inheritance base;
- the final input directory after any `--input_path` override;
- the output directory and whether it is empty or an intentional continuation;
- the effective dataset alias and scene name;
- camera dimensions after crop, depth scale, and (for TUM/ScanNet) distortion;
- selected split and effective frame count.

Do not let a stale inherited `dataset_name` survive a scene override, do not
use a dataset-specific path under another alias, and do not assume an output
path is created until the runtime has passed its own startup checks.
