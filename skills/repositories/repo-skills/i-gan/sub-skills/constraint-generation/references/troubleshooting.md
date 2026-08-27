# Constraint generation troubleshooting

Use this reference when dry validation, command construction, or native headless generation fails.

## Triage order

1. Run `python scripts/validate_constraint_inputs.py --help` to confirm the helper is available.
2. Validate the three constraint paths and dimensions.
3. Build a dry command with `scripts/build_constraint_command.py`.
4. Check model artifact readiness in the model-inference sub-skill.
5. Check Python/OpenCV/Theano/PyQt4 runtime imports only if native execution is requested.
6. Check CUDA/cuDNN/device flags only after Python imports and model files are correct.

Do not debug GPU failures before basic paths, image headers, and model artifacts are confirmed.

## Input validation failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `missing path` or `not a file` | Typo, wrong working directory, or generated file not created | Re-run with explicit paths or create the expected input triplet |
| `unreadable file` | Permission or broken file | Fix file permissions or regenerate the image |
| `unsupported or unrecognized image header` | Non-PNG/JPEG/BMP/GIF file, corrupt image, or format not covered by the safe validator | Convert to 8-bit PNG before native execution |
| `dimension mismatch` | Color, mask, and edge images were edited/exported at different sizes | Resize or recreate all three from one canvas |
| `does not match target size` in strict mode | Images are not the model resolution | Resize to the model resolution or remove `--strict-size` if native resizing is acceptable |
| Warning about mask channel | Mask is RGB/RGBA rather than grayscale | Ensure the first channel contains the intended mask, or convert to grayscale |

The validator intentionally does not import OpenCV. It cannot guarantee that OpenCV will decode every image exactly the same way, but it catches common mistakes safely.

## Command-builder failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `--top-k must be positive` | Invalid candidate count | Use `--top-k 1` or higher |
| `--batch-size must be positive` | Invalid latent batch count | Use `--batch-size 1` or higher |
| Warning that `top_k > batch_size` | More requested candidates than latent initializations | Lower `top_k` or raise `batch_size` |
| Shell command lacks `THEANO_FLAGS` | `--no-theano-flags` was passed | Add explicit Theano flags before native GPU execution |
| Output plan is too wide | Large `top_k` | Reduce `top_k` for a smaller visualization strip |

The command builder is dry-run only. It does not prove that the generated native command will execute.

## Native Python dependency failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError: No module named cv2` | OpenCV is missing from the native environment | Install an OpenCV build compatible with the chosen Python version, or switch to a prepared legacy environment |
| `ImportError: No module named theano` | Theano is missing | Use the legacy environment plan; modern drop-in replacements are not automatically compatible |
| `ImportError: No module named PyQt4` while running the headless script | The optimizer class imports `QThread` from PyQt4 even outside the GUI | Install PyQt4 in the legacy environment, or ask before patching/wrapping the optimizer for true headless execution |
| `ImportError` mentioning `lasagne` | Projection or predictor-related code path was invoked instead of plain constraint generation | Route projection work to image-projection and avoid importing projection modules for this workflow |
| `ImportError` mentioning `fuel` or `h5py` | Training/data code path was invoked | Route dataset/training work to training-data; plain headless generation should not require dataset loading |
| Syntax or print/import errors under modern Python | Python2-era source and dependencies | Prefer a known-compatible legacy Python environment; do not claim modern Python support without a real native run |

The repository documentation describes a Python2-era stack. Some files import `from __future__ import print_function`, but dependency compatibility is still the limiting factor.

## Theano/CUDA/cuDNN failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `nvcc` not found | CUDA toolkit is missing or not on `PATH` | Use a host with CUDA installed, or change Theano flags only if CPU execution is acceptable and tested |
| `cuDNN` or `dnn_conv` import/compile failure | Theano expects an older CUDA/cuDNN stack | Use a compatible legacy environment; do not assume current CUDA/cuDNN will work unchanged |
| `device=gpu0` unavailable | No visible NVIDIA GPU or invalid device index | Probe available devices and adjust `THEANO_FLAGS`, or stop with a GPU-backend blocker |
| Theano compilation hangs or is very slow | First-time Theano graph compilation | Explain that native execution compiles functions; use low `n_iters` for smoke runs after compilation completes |
| GPU out of memory | `batch_size` too high or GPU memory too small | Lower `batch_size`, lower `top_k`, close other GPU jobs, or use a larger GPU |
| `floatX` mismatch warnings | Theano flags not set to float32 | Use `floatX=float32` in `THEANO_FLAGS` for the documented workflow |

CPU Theano may compile some graphs, but the documented runtime expectation is GPU acceleration. Do not treat CPU-only import success as validation of native constrained generation.

## Model artifact failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No such file` for a model path | Model artifact was not downloaded or path was derived differently than expected | Route to model-inference to build or verify the model artifact path |
| `KeyError` for model configuration | Unknown `--model_name` or unsupported model config | Use a known model name or inspect model-inference's model list |
| Pickle load error | Corrupt, partial, or incompatible model artifact | Reacquire the artifact through the approved setup workflow |
| Shape mismatch during model load | Artifact does not match `model_name`/`model_type` | Use matching model flags and artifact file |
| Discriminator-related failure after setting `d_weight > 0` | Artifact lacks expected discriminator parameters or Theano graph fails | Retry with `--d_weight 0.0`; then investigate model artifact compatibility |

Do not invent model artifact names in this sub-skill. Model setup belongs to model-inference.

## Optimization behavior issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Output ignores color strokes | Color mask is empty, wrong first channel, or too small | Validate mask dimensions and inspect the first channel; use stronger/nonzero mask regions |
| Output ignores edge strokes | Edge first channel is empty or edges are low contrast | Use high-contrast edge strokes and ensure nonzero first-channel pixels mark constrained areas |
| Output looks unnatural | Constraints are too strong or conflict with model manifold | Reduce mask area, lower conflicting edges, try more random initializations, or tune `d_weight` carefully |
| All candidates look similar | Small `batch_size` or strong constraints collapse the search | Increase `batch_size` after smoke checks and keep `top_k <= batch_size` |
| Poor constraint satisfaction | Too few iterations or incompatible model domain | Increase `n_iters`, verify model domain, or adjust masks to match the model's training domain |
| Output strip contains fewer candidates than `top_k` | Internal cost threshold selected fewer low-cost candidates | This can be normal; reduce `top_k` or inspect constraints if too few candidates appear |
| Output strip is blank or black | Image transform mismatch, corrupt inputs, or model failure | Validate headers, try known-good sample-style inputs, and check model load logs |

## OpenCV image I/O problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Native crash at `im.shape` | OpenCV returned `None` for an unreadable image | Validate the path/header and convert the file to PNG |
| Colors appear swapped | BGR/RGB confusion in preprocessing or external image creation | The native script converts BGR to RGB; ensure external preprocessing did not already swap channels unexpectedly |
| Mask appears three-channel | OpenCV color-read mode expands grayscale files | This is expected; the native script uses the first channel |
| Output save returns no visible file | Output directory missing or OpenCV write failure | Create the output directory and verify write permissions before native execution |

## PyQt4 in a headless workflow

Although this workflow is non-UI, the optimizer wrapper subclasses `QThread`, so PyQt4 can still be imported during native execution. If a user cannot install PyQt4 but only needs scripted optimization, treat a patch or wrapper as a separate code-modification task and get explicit approval before changing native source behavior.

No `$DISPLAY` is usually a GUI launch issue, not a headless command issue. If the failure comes from UI windows, route to interactive-ui.

## Optional dependency routing

- OpenCV is required for the native headless script's image read/write path.
- PyQt4 may be required because of the optimizer class import.
- Theano and CUDA/cuDNN are required for the documented Theano optimizer path.
- Lasagne and AlexNet-related dependencies are projection concerns; route to image-projection.
- Fuel, HDF5 dataset tooling, and training cache files are training/data concerns.
- qdarkstyle is a GUI styling concern; route to interactive-ui unless import traces prove the headless path is loading UI code unexpectedly.

## Recovery templates

For a missing image:

```text
The dry validator cannot find <path>. Re-run from the directory that contains the constraint triplet or pass explicit paths. No native iGAN command was executed.
```

For a missing model:

```text
The constraint command is ready, but native execution is blocked because the model artifact is absent or unverified. Use the model-inference sub-skill to prepare the artifact, then rerun validation and the command builder.
```

For a legacy backend failure:

```text
The input contract is valid, but native execution is blocked by the legacy Theano/CUDA/PyQt4 stack. This sub-skill verifies dry planning only until a compatible environment is supplied.
```

For a low-quality native result:

```text
The native command completed, but the constraints are weak or conflicting. First inspect the mask first channels, then try a slightly larger batch size and more iterations. Keep top_k no larger than batch_size.
```
