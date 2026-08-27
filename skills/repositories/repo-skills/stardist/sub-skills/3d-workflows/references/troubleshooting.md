# 3D troubleshooting

Classify the failure before changing parameters. The required baseline is
CPU TensorFlow 2.x plus the compiled CPU StarDist extensions. CUDA execution,
OpenCL/gputools data generation, BioImage.IO, QuPath, and GUI integrations are
optional and must not be used to explain away a failed CPU baseline.

## Install and import

| Symptom | Diagnosis | Recovery/check |
|---|---|---|
| `import stardist` fails with missing TensorFlow/Keras/CSBDeep/SciPy/scikit-image | Base dependency or incompatible TensorFlow/Keras environment | Use an isolated environment, install TensorFlow 2.x before StarDist, then verify `import stardist`, `stardist.models`, `stardist.geometry`, and `stardist.data`. Do not copy a local environment path into runtime instructions. |
| Import fails in `stardist.lib` or a compiled `c_*` symbol is missing | StarDist CPU extension is absent or built for another Python/ABI/platform | Reinstall a compatible StarDist wheel or rebuild the package for the active Python; run a tiny `star_dist3D(..., mode="cpp")` and 3D NMS check. A Python-only fallback is not evidence of the required compiled baseline. |
| TensorFlow reports CUDA/cuDNN/cuFFT warnings but imports | Often an optional GPU/runtime warning, not an API failure | Check whether CPU model construction and inference work. CUDA support requires versions compatible with the installed TensorFlow; do not install historical setup files blindly. |
| `use_gpu=True` fails importing `gputools`, OpenCL, or device kernels | Optional OpenCL path unavailable | Set `use_gpu=False` for the required CPU generator, or explicitly prepare/prove gputools and an OpenCL runtime. A CUDA-visible device does not prove OpenCL support. |
| `star_dist3D(..., mode="opencl")` fails while `mode="cpp"` passes | Optional backend problem | Record OpenCL as optional/unverified; do not downgrade the CPU pass or silently switch the claimed backend. |
| `from stardist import ...` works but an example notebook cannot run | Notebook has extra Jupyter/data/plot/network requirements | Use the distilled Python recipe and local data. Notebooks are evidence, not runtime dependencies. |

## Axes, channels, and shape

| Symptom | Likely cause | Recovery/check |
|---|---|---|
| `axes` length/type error | Axis string does not have one label per image dimension | Use `ZYX` for a 3D single-channel array and `ZYXC` for channels-last data. Pass the actual input order, not the desired output order. |
| Channel-count assertion/value error | `n_channel_in` differs from image's `C` length | For `ZYX`, use `n_channel_in=1`; for `ZYXC`, set it to `img.shape[-1]`. Keep `n_tiles` channel entry at 1. |
| Labels have an unexpected channel axis | A channel was included in the expected output shape | Instance labels are spatial `ZYX`; `predict_instances_big` drops `C` from output. `labels_out.shape` must match spatial axes only. |
| Prediction appears transposed or anisotropy is reversed | `ZYX` versus `XYZ` convention was mixed | Preserve the array's actual order in `axes`; StarDist 3D ray vertices, points, grid, patches, and anisotropy use `Z,Y,X` order. Inspect a central XY and XZ slice before training. |
| Image/mask pair rejected by `StarDistData3D` | Spatial shape mismatch, mask has channels, or patch exceeds image | Assert `img.shape[:3] == mask.shape`, make `Y` integer `ZYX`, and ensure every image is at least `train_patch_size`. |
| `train_patch_size` divisibility error | Patch is not divisible by backbone/grid downsampling | Read the reported axis/divisor; increase or round each `(Z,Y,X)` patch dimension to a valid multiple. Do not fix by adding a channel dimension. |
| Boundary objects are systematically truncated | Model does not complete partially visible shapes | Treat image boundaries as incomplete instances; crop/annotate appropriately or exclude those objects from the intended claim. |

## Rays and anisotropy

| Symptom | Likely cause | Recovery/check |
|---|---|---|
| `dist` last dimension conflicts with ray length | `n_rays` and the ray object were selected separately | Use one ray instance, assert `config.n_rays == len(rays)`, and inspect loaded `config.rays_json`. Recreate NMS/rendering with exactly that ray definition. |
| `polyhedron_to_label` says inconsistent ray count or non-positive distances | Distances were truncated/reordered, or custom values are invalid | Ensure `dist.shape[-1] == len(rays)` and all distances are positive. Preserve `(Z,Y,X)` vertex order and use valid triangle faces. |
| Config warns about anisotropy mismatch | `Config3D.anisotropy` differs from serialized ray anisotropy | Decide one physical convention in `ZYX`, construct rays with it, and rebuild the config/model. Do not ignore the warning unless the mismatch is deliberate and tested. |
| Anisotropic objects look stretched/compressed | Tuple reversed, voxel calibration ignored, or rays not anisotropy-aware | Confirm the `ZYX` tuple against object extents/voxel spacing, use the same value in `Rays_GoldenSpiral` and `Config3D`, and compare reconstruction with a bounded label fixture. |
| `dist_loss_weights` expected to change standard training but does not | It is a ray utility, not a standard Config3D loss setting | `rays.dist_loss_weights(...)` returns one diagnostic/custom-loss weight per ray. `train_loss_weights` weights probability/distance/class heads, not individual rays. Implement and verify custom loss changes separately. |
| Custom `Rays_SubDivide` construction fails | `Rays_SubDivide` is an abstract base without `base_polyhedron()` | Use `Rays_Tetra`/`Rays_Octo`, or implement a tested subclass. Read `len(rays)` rather than estimating subdivision counts. |

## Model paths and weights

| Symptom | Likely cause | Recovery/check |
|---|---|---|
| `FileNotFoundError` loading local model | `config.json` is not under `basedir/name` | Given `StarDist3D(None, name=name, basedir=root)`, verify `root/name/config.json` exists and the model name has no typo. |
| No weights found or model loads random weights | HDF5 weights are absent/misnamed or not compatible | Put a compatible `weights_best.h5`/other HDF5 file beside config, or pass a valid model directory. Do not interpret a successful model construction as a trained-model check. |
| `from_pretrained("...")` lists models but does not return one | Name/alias is not registered or model assets are unavailable | Call `StarDist3D.from_pretrained()` to inspect registered names, use the exact alias, and allow the package's documented model retrieval/cache mechanism if permitted. |
| Config validation fails after loading | Saved config is stale or edited, with unsupported backbone/grid/rays/classes | Use the matching StarDist version/model assets; inspect `config.json` and do not hand-edit `n_rays`, `rays_json`, axes, or output channels independently. |
| Keras/TensorFlow load error for HDF5 weights | TensorFlow/Keras version or legacy weight format mismatch | Reproduce in a compatible TensorFlow 2.x environment. A CPU import pass does not prove weight-format compatibility. |

## Prediction, thresholds, and tiling

| Symptom | Likely cause | Recovery/check |
|---|---|---|
| `n_tiles must be an iterable of length ...` | Tile tuple does not match the input array dimensions | For `ZYX`, use three values; for `ZYXC`, use four with final value 1. |
| Error says only spatial axes can be tiled | A channel tile value is >1 or axes were misdeclared | Set `n_tiles[C]=1` and correct `axes`. |
| OOM with `predict_instances` | Dense map, too few tiles, high ray count, large channels, or scale-up | Keep `sparse=True`, increase spatial tile counts, lower tile/block dimensions, avoid `return_predict`, reduce channels/rays only as a quality decision, and use CPU/GPU memory diagnostics. |
| OOM with `sparse=True` | Raw volume/output assembly or NMS candidate set is still too large | Tile more aggressively, use a bounded probability threshold, process a volume block-wise with safe overlap/context, or stream into `labels_out` via `predict_instances_big`. |
| `scale` length/positive-factor error | Number/order of scale values does not match `axes` | Use scalar or one positive factor per input axis; spatial entries follow `Z,Y,X`, and `C` must be 1. |
| Scale output coordinates do not match a reference | Compared scaled coordinates to unscaled coordinates without the coordinate convention, or interpolation changed detections | Compare `points` after applying the intended spatial scale and inspect ray vertices; do not require identical labels when interpolation changes candidates. |
| Empty labels unexpectedly | Probability threshold too high, input not normalized, wrong axes, random/untrained weights, or object outside field of view | Check normalization, model weights, `axes`, `details["prob"]`, and a lower threshold on a bounded validation case. Do not fix quality by lowering thresholds without recording the change. |
| Too many/merged instances | Probability/NMS thresholds, ray resolution, anisotropy, or input normalization | Tune `prob_thresh`/`nms_thresh` on held-out labels with `optimize_thresholds`; confirm ray/grid/anisotropy first. |
| `return_predict=True` changes memory behavior | This option forces `sparse=False` | Remove it for production prediction; use `model.predict` explicitly on a bounded image if dense maps are needed. |
| Threshold optimization is unstable/slow | Too many validation volumes, broad threshold grids, or implicit tiling/memory pressure | Use a representative held-out subset, small explicit `nms_threshs`/`iou_threshs`, bounded `predict_kwargs`, and `save_to_json=False` for dry runs. Keep normalization fixed. |

## Big-volume block failures

Before `predict_instances_big`, verify **per axis**:

```python
assert min_overlap + 2 * context < block_size
```

Also ensure every predicted object is smaller than `min_overlap`, not merely
smaller than the median overlap. The function rounds values to the model grid,
so inspect its effective-value output.

| Symptom | Recovery |
|---|---|
| Assertion that overlap/context does not fit | Increase `block_size`, or lower context only if it remains at least the receptive-field requirement. Re-check the strict inequality after grid rounding. |
| Object violates `min_overlap` responsibility | Increase `min_overlap` beyond the object's full per-axis extent and increase block size to preserve the inequality. |
| Duplicate/missing seam labels | Correct axes, increase context and min-overlap, and compare with whole-volume prediction on a repeated small fixture. |
| `labels_out` shape error | Provide `(Z,Y,X)` in the order indicated by `axes`, with channels removed. |
| Channel blocks behave strangely | A `C` axis is intentionally processed as one full channel block. Use `ZYXC`, keep channel values non-spatial, and do not expect channel-wise block splitting. |
| Big prediction ignores requested options | It forces axes, labels, and non-sparse outer semantics needed for assembly. Apply only supported `predict_instances` kwargs and inspect the returned details. |

## Verification status boundaries

A CPU-safe ray/geometry check, a CPU compiled `star_dist3D` check, and a
small model construction/import check can establish baseline readiness. A
successful CPU check does **not** establish CUDA performance, OpenCL parity,
BioImage.IO conversion, QuPath behavior, or network model retrieval. Record
those as optional checks with their own dependency/hardware status.
