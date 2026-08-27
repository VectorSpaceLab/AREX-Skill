# Parameter and Library API Notes

Use this reference when reviewing or writing PyTracking parameter files, feature stacks, library utility calls, or checkpoint handoff code for a custom tracker.

## Parameter module essentials

A runtime parameter module lives under `pytracking/parameter/<tracker_name>/<param_name>.py` and must expose a zero-argument `parameters()` function returning a `TrackerParams` object.

```python
from pytracking.utils import TrackerParams
from pytracking.features.net_wrappers import NetWithBackbone


def parameters():
    params = TrackerParams()
    params.debug = 0
    params.visualization = False
    params.use_gpu = True

    params.image_sample_size = 18 * 16
    params.search_area_scale = 5
    params.net = NetWithBackbone(net_path='mytracker.pth.tar', use_gpu=params.use_gpu)

    return params
```

The evaluator imports the module and calls `parameters()` with no arguments. Avoid side effects at module import time; load networks lazily through wrappers or tracker `initialize_features()`.

## `TrackerParams`

Import with `from pytracking.utils import TrackerParams`.

Methods:

- `set_default_values(default_vals: dict)`: set missing attributes from a dictionary.
- `get(name: str, default?)`: return an attribute, an optional default, or raise if missing and no default is supplied.
- `has(name: str)`: check whether an attribute exists.

Common fields observed in built-in parameter files:

| Field | Purpose |
| --- | --- |
| `debug`, `visualization` | Runtime visual debug levels; evaluation may override these. |
| `use_gpu`, `device` | Backend selection. Existing trackers often set `device = 'cuda' if use_gpu else 'cpu'` during initialization when absent. |
| `image_sample_size`, `search_area_scale`, `feature_stride`, `train_feature_size` | Search crop and feature-grid geometry. These must match the trained network head. |
| `scale_factors`, `border_mode`, `patch_max_scale_change` | Patch sampling and scale handling. |
| `sample_memory_size`, `learning_rate`, `train_skipping` | Online model update behavior. |
| `advanced_localization`, threshold fields, `output_not_found_box` | Lost-target / distractor handling and output policy. |
| `vot_anno_conversion_type` | VOT polygon-to-rectangle conversion behavior for box trackers. |
| `object_presence_score_threshold` | Threshold added to final sequence outputs; defaults to `0.55` when absent. |
| `multiobj_mode`, `segmentation_threshold` | Multi-object wrapper behavior and mask merge threshold. |
| `net` | Runtime network wrapper for DiMP-like, ToMP-like, KeepTrack, KYS, LWL, RTS, and TaMOs-style trackers. |
| `features` | Feature extractor stack for ATOM/ECO-style trackers. |

## `FeatureParams` and `Choice`

Import with `from pytracking.utils import FeatureParams, Choice`.

`FeatureParams(**kwargs)` stores feature-specific attributes. If a provided value is a Python list, it is converted to a `TensorList`, which is useful for multi-resolution feature parameter lists.

`Choice(*args)` returns `random.choice(args)`. It is available for stochastic parameter selection but is not used by the current built-in parameter catalog. If you use it, document the nondeterminism and set seeds in the surrounding experiment when reproducibility matters.

## Tracker and parameter catalog

Built-in tracker packages:

| Tracker name | Implementation files | Runtime pattern |
| --- | --- | --- |
| `atom` | `atom.py`, `optim.py` | `params.features` with feature extractors and optimization utilities. |
| `dimp` | `dimp.py` | `params.net` with `NetWithBackbone`. |
| `dimp_simple` | `dimp_simple.py` | simplified DiMP-style `params.net` pattern. |
| `eco` | `eco.py`, `optim.py` | `params.features` with DCF/Fourier optimization utilities. |
| `keep_track` | `keep_track.py`, `candidates.py` | `params.net`, object presence scores, candidate association. |
| `kys` | `kys.py` | `params.net`, sequence-state prediction. |
| `lwl` | `lwl.py` | segmentation tracker with `params.net`, `segmentation_raw`, and custom merge. |
| `rts` | `rts.py`, `clf_branch.py`, `sta_helper.py` | segmentation + classifier tracker with mask-mode support. |
| `tamos` | `tamos.py` | multi-object-aware tracker with `params.net`; mode can be environment-controlled. |
| `tomp` | `tomp.py` | transformer-style box tracker with `params.net` and object presence scores. |

Parameter files by tracker:

| Tracker | Parameter names |
| --- | --- |
| `atom` | `atom_gmm_sampl`, `atom_prob_ml`, `default`, `default_vot`, `multiscale_no_iounet` |
| `dimp` | `dimp18`, `dimp18_vot18`, `dimp50`, `dimp50_vot18`, `dimp50_vot19`, `prdimp18`, `prdimp50`, `prdimp50_vot18`, `super_dimp` |
| `dimp_simple` | `super_dimp_simple` |
| `eco` | `default`, `mobile3` |
| `keep_track` | `default`, `default_fast` |
| `kys` | `default`, `default_vot` |
| `lwl` | `lwl_boxinit`, `lwl_ytvos` |
| `rts` | `rts50` |
| `tamos` | `tamos_resnet50`, `tamos_swin_base` |
| `tomp` | `tomp101`, `tomp50` |

Training settings that commonly feed runtime checkpoint handoff:

| Training module | Setting names |
| --- | --- |
| `bbreg` | `atom`, `atom_gmm_sampl`, `atom_paper`, `atom_prob_ml` |
| `dimp` | `dimp18`, `dimp50`, `prdimp18`, `prdimp50`, `super_dimp`, `super_dimp_simple` |
| `keep_track` | `keep_track` |
| `kys` | `kys` |
| `lwl` | `lwl_boxinit`, `lwl_stage1`, `lwl_stage2` |
| `rts` | `rts50` |
| `tamos` | `tamos_resnet50`, `tamos_swin_base` |
| `tomp` | `tomp101`, `tomp50` |

## Runtime checkpoint wrappers

### `NetWrapper` and `NetWithBackbone`

`NetWrapper(net_path, use_gpu=True, initialize=False, **kwargs)` defers loading until `initialize()`, then calls the PyTracking/LTR network loader. Attribute access is forwarded to the wrapped network.

`NetWithBackbone` adds image normalization, optional RGB/BGR handling, and `extract_backbone(im)` for trackers that consume backbone feature dictionaries or tensors.

Relative `net_path` values are resolved against the user's PyTracking `network_path` configuration. Absolute paths work but make parameter files less portable; use them only when the user explicitly wants that.

### Training-to-runtime handoff checklist

1. Identify the LTR training module and setting that produced the checkpoint.
2. Confirm the checkpoint file exists and has a constructor compatible with the runtime tracker class.
3. Put the checkpoint where PyTracking's runtime `network_path` can find it, or use a documented absolute path.
4. Set the parameter file's `net_path` to the selected checkpoint file name or path.
5. Keep geometry parameters synchronized with the training setting: feature size, stride, search area, crop mode, backbone/head type, and segmentation output size.
6. Validate the parameter module statically before running a tracker.

Do not start a training job or change training settings in this sub-skill; hand that task to `ltr-training`.

## Feature stack utilities

### Feature bases and extractors

- `FeatureBase`: base for single feature maps; implements color/grayscale gating, optional pooling, adaptive output size, and feature normalization.
- `MultiFeatureBase`: base for feature classes that emit multiple feature blocks.
- `SingleResolutionExtractor`: concatenates feature outputs at one stride.
- `MultiResolutionExtractor`: manages multiple feature blocks, patch extraction, per-feature params, strides, sizes, and color/gray filtering.
- `Concatenate`: combines feature classes with matching strides.

### Built-in feature classes

- `RGB`, `Grayscale`: simple normalized color/intensity features.
- `ResNet18m1`, `Mobilenet`, `ATOMResNet18`: deep feature wrappers that resolve pretrained network paths through the runtime configuration and provide layer stride/dimension metadata.
- `NetWithBackbone`: preferred wrapper for modern LTR-trained networks that expose backbone extraction.

### Preprocessing and augmentation

- `numpy_to_torch(a)`: convert an RGB NumPy image to shape `[1, C, H, W]` float tensor.
- `torch_to_numpy(a)`: inverse conversion for a single image tensor.
- `sample_patch(im, pos, sample_sz, output_sz=None, mode='replicate', max_scale_change=None, is_mask=False)`: crop and optionally resize a patch, returning both patch and coordinates.
- `sample_patch_multiscale(...)`: crop multiple scales and concatenate patches.
- `sample_patch_transformed(...)`: crop a patch and apply initialization transforms.
- Augmentation classes include identity, flips, translation, scaling, affine transforms, rotation, blur, and random affine variants.

Use `is_mask=True` when cropping masks to avoid bilinear interpolation and padding assumptions intended for images.

## Library utilities

PyTracking exposes selected utility modules through package-level imports.

| Utility | Use |
| --- | --- |
| `TensorList` | List-like tensor container with elementwise arithmetic, tensor-method forwarding, `apply`, `attribute`, `concat`, and `unroll`. |
| `TensorDict` | Tensor-oriented dictionary container. |
| `dcf` | Hann windows, Gaussian label functions, interpolation filters, regularization filters, and `max2d`. |
| `complex` | Complex-number operations using the repository's tensor representation. |
| `fourier` | Fourier sampling, shifting, summation, and inner products. |
| `optimization` | `L2Problem`, `MinimizationProblem`, conjugate-gradient, Gauss-Newton, Newton-CG, and gradient-descent optimizers used by ATOM/ECO-style online learning. |
| `operation` | Convolution helpers such as `conv2d` and `conv1x1`. |

When adapting older DCF/Fourier code, check the user's PyTorch version. Some older tensor FFT APIs differ from modern PyTorch; prefer preserving existing utility call patterns unless intentionally modernizing a tracker.

## Parameter review checklist

- `parameters()` exists, takes no required arguments, and returns a `TrackerParams` object.
- Import-time code does not load datasets, checkpoints, GUI windows, or run training/evaluation.
- `debug` and `visualization` have safe defaults.
- `use_gpu` is explicit and device handling is consistent with the user's environment.
- Checkpoint `net_path` exists under the runtime network path or is deliberately absolute.
- Search geometry and network head expectations match the chosen checkpoint.
- Multi-object and segmentation flags are explicit when the tracker needs them.
- Run the bundled static validator before trying a real tracker run.
