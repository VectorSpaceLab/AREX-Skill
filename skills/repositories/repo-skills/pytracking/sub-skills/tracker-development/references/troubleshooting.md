# Tracker Development Troubleshooting

Start with the static validator before importing or running a custom tracker:

```bash
python skills/disco/pytracking/sub-skills/tracker-development/scripts/validate_tracker_layout.py \
  --repo-root /path/to/pytracking-checkout \
  --tracker-name mytracker \
  --param-name default
```

The validator is read-only and does not import PyTracking by default.

## Fast symptom map

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: pytracking.tracker.<name>` | Tracker folder is missing, misnamed, or not a Python module. | Create `pytracking/tracker/<name>/__init__.py`; ensure `<name>` is a valid Python identifier and matches the tracker command/API argument. |
| `AttributeError: module ... has no attribute get_tracker_class` | Tracker package `__init__.py` does not define `get_tracker_class()`. | Add `from .<file> import <Class>` and `def get_tracker_class(): return <Class>`. Keep it lightweight. |
| Import error from tracker `__init__.py` | Wrong relative import, class renamed, implementation file missing, or import-time heavy dependency failure. | Fix relative import first. Move checkpoint/dataset/GUI loading out of import time and into `initialize_features()` or `initialize()`. |
| Tracker class does not initialize | It does not inherit `BaseTracker`, overrides `__init__` without `super()`, or lacks expected fields. | Inherit `BaseTracker`; if overriding `__init__`, call `super().__init__(params)`. Ensure `self.params` and `self.visdom` exist. |
| `ModuleNotFoundError: pytracking.parameter.<tracker>.<param>` | Parameter folder or file is missing/misnamed. | Add `pytracking/parameter/<tracker>/<param>.py` and `__init__.py`; pass `<param>` without `.py`. |
| `AttributeError: parameters` | Parameter file does not define `parameters()`. | Add a zero-argument `parameters()` function returning `TrackerParams`. |
| `parameters() takes ... arguments` | PyTracking calls `parameters()` with no arguments. | Move user choices into attributes or separate parameter files; keep the function zero-argument. |
| Parameter object lacks `.get()` or `.has()` | `parameters()` returned a dict or custom object instead of `TrackerParams`. | Return `TrackerParams()` and set fields as attributes. |
| `Failed to load network` or `No matching checkpoint file found` | `net_path` is wrong, checkpoint is not under runtime `network_path`, or an intended training checkpoint was not copied. | Verify the selected `.pth` / `.pth.tar` exists. Put it under the configured network path or use an approved absolute path. If it must be trained, route to `ltr-training`. |
| Checkpoint constructor or state-dict mismatch | Runtime tracker expects a different network architecture than the trained checkpoint provides. | Match training setting, parameter geometry, and tracker network API. Do not swap DiMP/ToMP/LWL/RTS checkpoints blindly. |
| CUDA error or CPU fallback failure | `params.use_gpu` conflicts with available hardware or the network requires CUDA. | Set `params.use_gpu` deliberately; route environment/backend verification or actual runs to the appropriate execution sub-skill. |
| KeyError for `target_bbox` during visualization or result saving | `track()` did not return `target_bbox`, or returned it under a different key. | Return `{'target_bbox': [x, y, w, h]}` for single-object tracking every frame. |
| Boxes draw in the wrong location | Box order was interpreted incorrectly. | Use `[top_left_x, top_left_y, width, height]`, not `[y, x, h, w]` and not corner coordinates. Clip only if the tracker's algorithm requires it. |
| Results show `[-1, -1, -1, -1]` unexpectedly | `output_not_found_box` or lost-target logic is too aggressive. | Review not-found thresholds, score preprocessing, search area scale, and recovery behavior. |
| `previous_output['segmentation_raw']` missing | A segmentation tracker expects raw/probability masks but initialization or the previous track step did not emit them. | Emit `segmentation_raw` consistently from `initialize()` and `track()` when the next frame needs it. |
| VOT mask mode still reports rectangles | `predicts_segmentation_mask()` was not overridden or returns `False`. | Override it to return `True` for mask-output trackers. |
| Multi-object boxes have wrong ids | Object id keys changed type or got remapped inconsistently. | Preserve object ids from `info['object_ids']` / `init_object_ids`; for merged segmentation masks, use pixel value `0` for background and target ids for objects. |
| Multi-object wrapper ignores custom merge behavior | `merge_results(out_all)` is missing or attached to the wrong class. | Implement `merge_results` on the tracker class returned by `get_tracker_class()` when default merge is insufficient. |
| Single-object tracker fails on multiple targets | `multiobj_mode` is `default` but the tracker only handles one object. | Set `multiobj_mode = 'parallel'` unless the class handles full object-id mappings internally. |
| GUI/Visdom errors while debugging | Debug visualization requires optional services or display support. | Keep `params.debug = 0` and `params.visualization = False` for safe default parameter files; route actual visualization runs to `tracking-evaluation`. |
| Parameter edits appear to have no effect | Evaluation is running a different parameter name or stale checkpoint. | Confirm tracker and parameter names passed to the command/API. Validate the selected parameter file and checkpoint path. |
| Random results across runs | `Choice()` or random initialization/augmentation is used without seed control. | Avoid `Choice()` in production parameter files, or document and seed the experiment at the evaluation layer. |
| FFT or complex tensor errors | Older DCF/Fourier utility assumptions differ from the user's PyTorch version. | Prefer existing PyTracking utility functions; if modernizing FFT code, isolate and test with tiny tensors before running trackers. |

## Debugging workflow

1. **Static layout check**: run the bundled validator with the selected tracker and parameter names.
2. **Read parameter side effects**: ensure module import does not load networks, datasets, GUI windows, or train/evaluate anything.
3. **Check registration**: `get_tracker_class()` should return the class object, not an instance.
4. **Check initialization keys**: make sure `initialize()` handles `init_bbox`, optional `init_mask`, and multi-object init fields if relevant.
5. **Check output keys**: make sure `track()` returns `target_bbox` in `[x, y, w, h]` order and emits segmentation fields only when they are full-frame aligned.
6. **Check checkpoint handoff**: verify `net_path`, architecture, and geometry against the intended LTR training setting.
7. **Then hand off execution**: once static checks pass, use `tracking-evaluation` for a real dataset/video run.

## Common code fixes

### Minimal registration fix

```python
from .mytracker import MyTracker


def get_tracker_class():
    return MyTracker
```

### Minimal parameter fix

```python
from pytracking.utils import TrackerParams


def parameters():
    params = TrackerParams()
    params.debug = 0
    params.visualization = False
    params.use_gpu = True
    return params
```

### Minimal output fix

```python
def track(self, image, info=None):
    # compute x, y, w, h
    return {'target_bbox': [x, y, w, h]}
```

### Safe lazy network initialization

```python
def initialize_features(self):
    if not getattr(self, 'features_initialized', False):
        self.params.net.initialize()
    self.features_initialized = True
```

Call `initialize_features()` from `initialize()` after device fields are settled, not at module import time.

## When to route elsewhere

- Need to run `run_tracker`, `run_video`, `run_webcam`, or `run_experiment`: route to `tracking-evaluation`.
- Need to train a checkpoint, change LTR train settings, inspect dataset loaders, or run CUDA training smoke: route to `ltr-training`.
- Need to score saved results, plot curves, package GOT-10k/TrackingNet outputs, or plan VOT submission integration: route to `analysis-and-packaging`.
