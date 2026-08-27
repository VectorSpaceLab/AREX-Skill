# PyTracking Tracker Extension Guide

This guide covers custom tracker and parameter-module work only. Running the tracker belongs to `tracking-evaluation`; training a network belongs to `ltr-training`; analyzing saved outputs belongs to `analysis-and-packaging`.

## Runtime import model

PyTracking selects trackers by **module names**, not by class names. The evaluation wrapper constructs imports equivalent to:

- tracker package: `pytracking.tracker.<tracker_name>`
- parameter module: `pytracking.parameter.<tracker_name>.<param_name>`

That means a new tracker named `mytracker` should normally add:

```text
pytracking/tracker/mytracker/
  __init__.py
  mytracker.py
pytracking/parameter/mytracker/
  __init__.py
  default.py
```

The tracker package name and parameter folder name should match the tracker name passed to PyTracking commands or APIs. The parameter file stem is the parameter name.

## Tracker registration

The tracker package `__init__.py` must expose `get_tracker_class()` and return the tracker class object. Keep this file lightweight; do not load checkpoints here.

```python
from .mytracker import MyTracker


def get_tracker_class():
    return MyTracker
```

The implementation class should inherit `BaseTracker`:

```python
from pytracking.tracker.base import BaseTracker


class MyTracker(BaseTracker):
    multiobj_mode = 'parallel'  # or omit / use 'default' when handling multi-object internally

    def initialize(self, image, info: dict) -> dict:
        ...

    def track(self, image, info: dict = None) -> dict:
        ...
```

## `BaseTracker` contract

`BaseTracker.__init__(params)` stores `self.params` and initializes `self.visdom = None`. Existing trackers usually rely on this inherited constructor and do not override it unless they call `super().__init__(params)`.

### `initialize(self, image, info)`

Called on the first frame or when a new object is initialized. Expect:

- `image`: RGB image as a NumPy array.
- `info['init_bbox']`: target box in `[top_left_x, top_left_y, width, height]` order for single-object calls.
- `info['init_mask']`: optional full-image mask for segmentation-capable datasets or VOT mask initialization.
- `info['object_ids']`, `info['init_object_ids']`, `info['sequence_object_ids']`: present in multi-object contexts.
- `info['init_other']`: present when the multi-object wrapper splits initialization information for each target.

Typical responsibilities:

1. Convert the image with `numpy_to_torch()` if using PyTorch features.
2. Read the initial box or mask and initialize target center, size, scale, memory, filters, or network state.
3. Lazily initialize features or networks through an `initialize_features()` helper if checkpoint loading is expensive.
4. Return a dictionary. Returning `None` is tolerated on initialization, but returning timing and segmentation information is clearer.

For frame zero, the evaluator supplies defaults for `target_bbox`, `time`, `segmentation`, and `object_presence_score` when they are absent.

### `track(self, image, info=None)`

Called for each following frame. Expect:

- `image`: RGB image as a NumPy array.
- `info['previous_output']`: an ordered copy of the previous frame's tracker output, including extra fields such as `segmentation_raw` when the tracker emitted them.
- Possible new-object initialization fields in video/webcam or multi-object runs.

Return a dictionary every frame. `target_bbox` is the central output key for box tracking and should be present unless the tracker is intentionally initialization-only.

## Output dictionary keys

| Key | Shape / type | Use |
| --- | --- | --- |
| `target_bbox` | single object: `[x, y, w, h]`; multi-object: mapping object id -> box | Primary bounding-box prediction. Required by normal evaluation and visualization. |
| `time` | float seconds | Optional. The evaluator or wrapper fills defaults in common paths. |
| `segmentation` | full-image NumPy mask/probability; multi-object merged mask uses label `0` for background and object ids for targets | Used by VOS/VOT mask modes and visualization. |
| `segmentation_raw` | raw logits or probabilities; single object array or object-id mapping | Used by segmentation trackers to update from `previous_output` and to merge multi-object masks. |
| `segmentation_soft` | per-object soft mask | Optional input to the default multi-object merge when present. |
| `object_presence_score` | float or object-id mapping | Optional confidence/lost-target signal. The evaluator adds `object_presence_score_threshold` from params, defaulting to `0.55`. |
| `clf_target_bbox`, `clf_search_area`, `segm_search_area` | box or search-area diagnostics | Optional debug/visualization fields; they are not primary persisted result fields. |
| `init_mask` | tensor/array created during initialization | Optional internal signal for segmentation trackers. |

The sequence evaluator stores lists for `target_bbox`, `time`, `segmentation`, and `object_presence_score`, then adds `image_shape` and `object_presence_score_threshold` to the final result dictionary. Extra keys can still matter because they are passed forward in `previous_output` and can be used for visualization.

## Multi-object conventions

PyTracking has two common modes:

- `multiobj_mode = 'parallel'`: the evaluator wraps the tracker in a multi-object wrapper. The wrapper creates one tracker instance per object, splits `init_bbox`/`init_mask`, calls each per-object tracker, and merges outputs. This is the simplest path for a single-object tracker that should work on multiple targets.
- `multiobj_mode = 'default'` or omitted: the tracker class itself handles the full multi-object state. Use object-id mappings for boxes and confidence scores, and handle `init_object_ids` / `sequence_object_ids` directly.

For `parallel` mode, a per-object tracker can emit single-object boxes and masks. If it implements `merge_results(out_all)`, that method controls how object outputs are combined. Otherwise the default merge stacks `segmentation_soft` or `segmentation`, thresholds by `params.segmentation_threshold` or `0.5`, and builds object-id dictionaries for non-segmentation fields.

For custom multi-object trackers, keep id types stable. The video/webcam path draws `target_bbox` mappings by object id, and VOS segmentation expects pixel labels to be object ids with `0` reserved for background.

## Segmentation conventions

- Override `predicts_segmentation_mask()` to return `True` if the tracker should use mask mode in VOT-style integrations.
- When initializing from a box, segmentation trackers may synthesize an initial mask; when initializing from a mask, preserve it as a full-image mask aligned to the input frame.
- `segmentation` should be a full-image mask for the current frame, not just a search crop.
- For iterative segmentation trackers, `segmentation_raw` is often needed because the next frame reads `info['previous_output']['segmentation_raw']`.
- For multi-object segmentation, merge outputs into a label image where each target id has its own integer label.

## Parameter module contract

Every parameter file must define:

```python
from pytracking.utils import TrackerParams


def parameters():
    params = TrackerParams()
    params.debug = 0
    params.visualization = False
    params.use_gpu = True
    ...
    return params
```

Use `params.net` for trackers that expect a network wrapper such as `NetWithBackbone`. Use `params.features` for trackers built around feature extractors such as `MultiResolutionExtractor`. See [parameter-and-library-api.md](parameter-and-library-api.md) for API details and catalogs.

## Training-to-runtime checkpoint handoff

A training setting creates a checkpoint; a runtime parameter file points the tracker to that checkpoint. Keep the two steps separate:

1. Use `ltr-training` to train or select a checkpoint.
2. Place or symlink the selected `.pth` / `.pth.tar` file where the user's PyTracking `network_path` can find it, or use an explicit absolute path if the user approves.
3. In the parameter module, set a runtime wrapper such as `NetWithBackbone(net_path='mytracker_ep0050.pth.tar', use_gpu=params.use_gpu)`.
4. Match the runtime tracker class to the checkpoint constructor and expected network API. A box tracker may expect classifier and box-regressor methods; segmentation trackers may expect decoder or `segment_target` methods.
5. Validate the tracker and parameter layout before running an evaluation command.

If the checkpoint does not exist yet, stop this workflow and route training to `ltr-training` rather than starting training here.

## Static validation

Use the bundled validator before importing heavy tracker code:

```bash
python skills/disco/pytracking/sub-skills/tracker-development/scripts/validate_tracker_layout.py \
  --repo-root /path/to/pytracking-checkout \
  --tracker-name mytracker \
  --param-name default
```

The validator checks module paths, `get_tracker_class()`, implementation class shape, and `parameters()` without loading checkpoints or datasets.
