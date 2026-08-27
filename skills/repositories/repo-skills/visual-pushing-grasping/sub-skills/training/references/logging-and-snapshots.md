# Logging, snapshots, and resume

`Logger` owns a session tree, while `Trainer.preload` reconstructs the
iteration and in-memory histories needed for resume and replay. Treat the tree
as a compatibility contract, not as a generic log directory.

## Session layout

A new run uses the effective logging parent (source default: `logs`) and
creates a child named with local time in the form `YYYY-MM-DD.HH:MM:SS`.
`--continue_logging` instead treats `--logging_directory` as the already
existing session root. The logger creates or expects:

```text
SESSION/
  info/
    camera-intrinsics.txt
    camera-pose.txt
    camera-depth-scale.txt
    heightmap-boundaries.txt
    heightmap-resolution.txt
  data/
    color-images/
    depth-images/
    color-heightmaps/
    depth-heightmaps/
  models/
  visualizations/
  recordings/
  transitions/
    data/
```

The main loop writes RGB-D images and valid RGB-D heightmaps each iteration.
Color images are saved in OpenCV BGR file order after conversion. Raw depth
images are rounded at `1e-4` meters; heightmap depth is rounded at `1e-5`
meters. A replay read of a heightmap depth file must divide by `100000` and
use the color conversion shown in the source. Do not treat these PNGs as
lossless floating-point arrays.

`info/` records camera and heightmap metadata for the session. This route does
not interpret calibration or workspace geometry; ask the geometry route when
metadata and pixels disagree.

## Transition logs

`write_to_log(name, values)` writes a space-delimited file at
`transitions/<name>.log.txt`. The action/training loop maintains:

| File | Meaning |
|---|---|
| `executed-action.log.txt` | rows `[primitive_id, rotation, y, x]`; primitive `0` is push and `1` is grasp |
| `label-value.log.txt` | reactive binary label or reinforcement target |
| `reward-value.log.txt` | reactive label duplicate or reinforcement immediate reward |
| `predicted-value.log.txt` | selected map value before execution |
| `use-heuristic.log.txt` | `1` when a handcrafted primitive selector was used |
| `is-exploit.log.txt` | `1` for exploitation and `0` for exploration |
| `clearance.log.txt` | iteration values when the table/scenario is reset |

The first six per-action histories are rewritten every time an event is
appended. Clearance is written when the environment is considered empty or
stuck. Evaluation and plots may consume these logs, but their metric formulas
belong to the evaluation route.

## Snapshots

During training, the logger saves:

- `models/snapshot-backup.<method>.pth` after each training iteration; and
- `models/snapshot-<six-digit-iteration>.<method>.pth` every 50 iterations.

Each file is a PyTorch `state_dict`, not a serialized `Trainer`, optimizer, or
replay buffer. `save_model` temporarily moves the model to CPU before saving;
the main loop moves it back to CUDA afterward when needed. Testing does not
save snapshots. A snapshot file is not evidence that its original optimizer,
pretrained trunk download, Python version, or torch/torchvision ABI is
available.

## Resume contract

A training resume needs both:

```text
--load_snapshot --snapshot_file SESSION/models/snapshot-backup.<method>.pth
--continue_logging --logging_directory SESSION
```

The source loads the state dict before logger creation, then `preload` reads
all transition logs and sets `iteration` from the executed-action history
(`number of rows - 2` in the historical implementation). It truncates the
per-action arrays to that iteration and reshapes scalar logs to `(iteration,1)`.
This is why a partial last line, one-row `numpy.loadtxt` result, or a session
from a different method can fail in surprising ways.

Before a resume, verify without loading torch:

1. snapshot is a non-empty regular file and its method suffix agrees with
   `--method`;
2. session root and `transitions/` exist;
3. all seven log files exist, are non-empty, and contain parseable numeric
   whitespace-delimited rows;
4. action rows have four numeric columns and primitive IDs are `0` or `1`;
5. scalar histories have enough rows for the action history; and
6. replay image pairs exist for any history indices that will be sampled.

The bundled validator performs path and log-shape checks, but cannot prove
state-dict key compatibility. Keep a copy of the session and never overwrite
the only snapshot while diagnosing a resume.

## Missing or new logs

For a new run omit `--continue_logging`; the logger will create a fresh
session under the effective parent. Do not point a new run at an old session
just to reuse its directory. For a resume, do not create empty placeholder
logs: `np.loadtxt` and replay need real aligned histories. Restore the session
from backup or stop and report the missing artifact. If only visualizations or
recordings are missing, they are not required by `preload`; if any transition
history is missing, treat the resume as blocked.
