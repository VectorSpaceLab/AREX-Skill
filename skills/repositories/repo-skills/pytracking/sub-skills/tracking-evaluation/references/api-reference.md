# Tracking/Evaluation API Reference

## When to read

Read this when using PyTracking from Python instead of running the native scripts. The signatures below were verified in an inspection environment; they are concise route facts, not a replacement for execution-time validation of data paths and checkpoints.

## Public imports

```python
from pytracking.evaluation import Tracker, trackerlist, get_dataset, get_dataset_attributes
from pytracking.run_tracker import run_tracker
from pytracking.run_video import run_video
from pytracking.run_webcam import run_webcam
from pytracking.run_experiment import run_experiment
```

## Verified signatures

```python
Tracker(name: str, parameter_name: str, run_id: int = None, display_name: str = None)
```

`Tracker` wraps a tracker class and computes result/segmentation output directories from the local evaluation environment. It imports `pytracking.tracker.<name>` and expects that module to expose `get_tracker_class()`.

```python
trackerlist(name: str, parameter_name: str, run_ids=None, display_name: str = None)
```

Returns a list of `Tracker` objects. If `run_ids` is `None` or an integer, it is normalized to a one-element list.

```python
get_dataset(*args, **kwargs)
```

Loads one or more dataset aliases and returns a `SequenceList` containing sequences from every alias. Use aliases from [datasets and results](datasets-and-results.md).

```python
run_tracker(tracker_name, tracker_param, run_id=None, dataset_name='otb', sequence=None, debug=0, threads=0, visdom_info=None)
```

Runs a tracker on an alias-selected dataset. `sequence` can be `None`, a sequence name, or an integer-like index. `visdom_info` is a dict such as `{'use_visdom': False, 'server': '127.0.0.1', 'port': 8097}`.

```python
run_video(tracker_name, tracker_param, videofile, optional_box=None, debug=None, save_results=False)
```

Runs a tracker on a video file. `optional_box` is `[x, y, width, height]`. When omitted, target selection is interactive.

```python
run_webcam(tracker_name, tracker_param, debug=None, visdom_info=None)
```

Runs webcam tracking using camera index 0 and interactive box selection.

```python
run_experiment(experiment_module: str, experiment_name: str, debug=0, threads=0)
```

Imports `pytracking.experiments.<experiment_module>`, calls the named function, and expects `(trackers, dataset)`.

## Tracker sequence output contract

`Tracker.run_sequence(...)` delegates to a concrete tracker and stores output fields produced by `initialize()` and `track()`:

- `target_bbox`: `[x, y, width, height]` for single-object mode or an ordered mapping from object id to box for multi-object mode.
- `time`: per-frame timing.
- `segmentation`: optional mask output.
- `object_presence_score`: optional confidence score, with `object_presence_score_threshold` defaulting to `0.55` if the tracker has no parameter override.
- `image_shape`: added for OxUvA-style output handling.

## Multi-object and segmentation notes

- If a tracker class or parameter sets `multiobj_mode='parallel'`, PyTracking can wrap the tracker through `MultiObjectWrapper` for multiple target objects.
- Segmentation trackers should implement `predicts_segmentation_mask()` when VOT/VOS integration needs to know the output type.
- Video/webcam mode stores boxes by object id when `save_results=True`.

## Safe API use pattern

```python
from pytracking.run_tracker import run_tracker

run_tracker(
    tracker_name='dimp',
    tracker_param='dimp50',
    dataset_name='otb',
    sequence='Soccer',
    debug=0,
    threads=0,
    visdom_info={'use_visdom': False},
)
```

Before running the call, validate local paths and checkpoint availability with the root setup checker and this sub-skill's dataset guidance.
