# Deployment troubleshooting matrix

| Symptom | Diagnosis and recovery |
|---|---|
| `--help` imports TensorFlow or fails from another cwd | Use the bundled adapter; its imports are delayed. Run it directly from a temporary cwd and check that no source path is injected. |
| `--axes` cannot be combined with `--model` | The original parser grouped later options accidentally. Use the adapted script or verify the installed entry point's help; only model selection is required. |
| Missing/unknown model | Existing directory must contain `config.json` and `.h5` weights. A plain pretrained name can need network/cache; a missing path-like selector is not a download request. |
| Pretrained retrieval hangs/checksum fails | Bound network/cache use or use a reviewed local model. Record resource and checksum status; do not claim a successful local CLI check. |
| Input missing, directory, or unexpected suffix | Resolve shell expansion and permissions. 3D requires `.tif`/`.tiff`; quote paths and inspect the input list. |
| Rank/axes error | Read image shape and declare exactly `YX`/`YXC` or `ZYX`/`ZYXC`; channel is not batch/time. Split time or use the owning API workflow. |
| Output shape includes a channel or wrong spatial order | Check the declared axes and model dimensionality. CLI outputs labels only and must omit `C`. |
| Empty predictions | Inspect raw range, normalization, modality, axes, and model weights before tuning probability/NMS thresholds in the owning workflow. Empty ROI/OBJ may be valid but is not proof of correctness. |
| Output is float or viewer rejects labels | Confirm returned `labels` is integer and spatially shaped before handoff. Do not round normalized floats into ground truth. |
| Output exists or equals input | Choose a new name or consciously use `--overwrite`; input overwrite is always refused. |
| Output template escapes directory | Use a plain filename such as `{img}.stardist.tif`. The adapter rejects absolute/nested templates, duplicate names, and symlink targets outside `--outdir`. |
| ROI export raises | Pass `polys['coord']` from a 2D `predict_instances` result, not `labels` or a 3D dictionary. Check row/column vertex shapes. |
| ROI ZIP opens empty | No objects survived, or the wrong result was passed. Count `.roi` members; position metadata is 1-based by default. |
| OBJ missing keys/shape error | Pass the complete 3D dictionary (`dist`, `points`, `rays_vertices`, `rays_faces`) and check `(N,R)`, `(N,3)`, `(R,3)`, `(F,3)`. |
| OBJ rotated/wrong scale | StarDist arrays are Z/Y/X but OBJ vertices are written X/Y/Z. Pass physical scale as `(z,y,x)` and retain it in a sidecar. |
| OBJ has no vertices/faces | Prediction is empty or geometry is malformed. Treat empty output separately from an export failure. |
| BioImage.IO import unavailable | Install `stardist[bioimageio]` only in an isolated approved environment or record `SKIP_OPTIONAL_BIOIMAGEIO`. |
| BioImage.IO mode/model rejected | Use `tensorflow_saved_model_bundle` for a non-multiclass model. The helper rejects `keras_hdf5` and baseline SavedModel multiclass export. |
| BioImage.IO axes/test input failure | Use representative float32 data with matching `YX`/`YXC` or `ZYX`/`ZYXC` axes and dimensions compatible with model grid/halo. |
| BioImage.IO validator/network failure | Separate local ZIP/schema errors from unavailable remote resources. Preserve an optional unresolved result. |
| BioImage.IO destination exists | Choose a fresh path; import intentionally refuses to overwrite. Compare config, thresholds, and weights after success. |
| QuPath classes missing | Install/enable the external ImageJ extension and use a compatible QuPath API. Static checks cannot prove GUI execution. |
| QuPath objects missing | Ensure annotations are in the hierarchy; rectangles are intentionally skipped. Run for project with a selected image. |
| QuPath output overwritten/shifted | Use a project copy, inspect existing filenames, and verify `downsample` and channel selection for both image and mask. |
| CPU extension import fails | Verify the prepared CPU StarDist/TensorFlow environment and compiled extensions. CUDA/OpenCL does not repair a missing CPU extension. |
| OpenCL/gputools error | OpenCL is optional; record `SKIP_OPTIONAL_OPENCL` and use CPU. Visible CUDA hardware is not evidence of OpenCL compatibility. |
| Viewer calibration is wrong | Keep axes, voxel scale, downsample, normalization, model provenance, and export settings in a sidecar record; ROI/OBJ/TIFF consumers do not share all metadata. |

## Minimal diagnostic sequence

```bash
python /path/to/predict2d.py --help
python /path/to/predict3d.py --help
python - <<'PY'
import inspect
from stardist.models import StarDist2D, StarDist3D
print(inspect.signature(StarDist2D.predict_instances))
print(inspect.signature(StarDist3D.predict_instances))
PY
```

Run only the failing surface next: local model load, TIFF read, one small CPU
prediction, archive/OBJ inspection, optional import, or external GUI check.
Do not combine model download, optional dependency installation, and output
conversion in one unbounded retry.
