# FastReID modeling and inference troubleshooting

## Missing weights or checkpoint path

Symptoms:

- `AssertionError: Checkpoint ... not found!`
- Inference produces features but they are semantically meaningless.
- Shape mismatch warnings while loading classifier/head parameters.

Resolution:

1. Confirm whether the workflow is only a smoke check or real ReID inference.
2. For smoke checks, do not load weights; set `MODEL.BACKBONE.PRETRAIN=False` and leave `MODEL.WEIGHTS` empty.
3. For real inference, require an explicit local `.pth` checkpoint matching the model config.
4. If classifier weights mismatch because the number of training identities differs, report the mismatch. Feature extraction can sometimes still be used if the feature layers load, but benchmark claims require a matching checkpoint.

## Unwanted pretrain downloads

Symptoms:

- Model construction stalls or attempts network access.
- A backbone builder tries to resolve an ImageNet/pretrain artifact.

Resolution:

- For offline or CPU-only checks, set `cfg.MODEL.BACKBONE.PRETRAIN = False` before `build_model(cfg)` or `build_backbone(cfg)`.
- Do not rely on recipe defaults: many strong recipes enable pretraining.
- If the user explicitly needs pretrained backbone initialization, ask for a local `MODEL.BACKBONE.PRETRAIN_PATH` or explicit network permission.
- Bundled smoke scripts force `PRETRAIN=False` by default.

## CPU/CUDA device mismatch

Symptoms:

- `RuntimeError: Expected all tensors to be on the same device...`
- `AssertionError: Torch not compiled with CUDA enabled`
- Slow or failed inference when a config default expects CUDA.

Resolution:

1. For portable smokes, set `cfg.MODEL.DEVICE = "cpu"`.
2. Move the input tensor to the model device if writing custom inference code.
3. Do not set `cuda`, `cuda:0`, or parallel predictor modes unless the Python environment has CUDA-enabled PyTorch and visible GPUs.
4. Remember FastReID's default device is `cuda`, so a config that looks otherwise minimal can still fail on CPU-only installs.

## Tensor shape, dtype, or color-space errors

Symptoms:

- Convolution errors mentioning channel count.
- Pooling/head errors after unusual image dimensions.
- Features look inconsistent between OpenCV image inference and tensor inference.

Resolution:

- Input tensors must be shaped `(B, 3, H, W)` and normally use `float32`.
- Demo-style image input starts as BGR HWC from OpenCV, is converted to RGB HWC, resized to `INPUT.SIZE_TEST`, transposed to CHW, then batched.
- `INPUT.SIZE_TEST` is `[height, width]`; OpenCV resize uses `(width, height)`.
- Pixel values should usually remain in 0-255 scale before entering the model because the Baseline meta-architecture applies `MODEL.PIXEL_MEAN` and `MODEL.PIXEL_STD` internally.
- Set `model.eval()` for feature extraction; training mode expects `targets` and returns losses.

## `evaluate_rank` import mismatch

Symptom:

```text
ImportError: cannot import name 'evaluate_rank' from 'fastreid.evaluation'
```

Cause:

- In this checkout, `evaluate_rank` is defined in the rank submodule but is not re-exported by the package-level evaluation namespace.

Resolution:

```python
from fastreid.evaluation.rank import evaluate_rank
```

Use this import for custom metric/debug code. If adapting an older visualization or evaluation helper that imports from `fastreid.evaluation`, patch the import to the submodule form above.

## Cython rank fallback warning

Symptom:

```text
Cython rank evaluation ... is unavailable, now use python evaluation.
```

Meaning:

- The optional compiled rank extension is not available.
- The pure-Python rank implementation is used instead.

Resolution:

- For small smoke checks, the Python fallback is acceptable.
- For large benchmark evaluation, install/build the optional Cython rank extension in a compatible environment or expect slower rank metric computation.
- To make fallback explicit in code, call `evaluate_rank(..., use_cython=False)`.

## Missing OpenCV (`cv2`)

Symptoms:

- `ModuleNotFoundError: No module named 'cv2'`
- Image feature smoke cannot read or resize a user image.

Resolution:

- Install an OpenCV package compatible with the environment, such as a headless build for servers.
- If the task is only model construction, use `scripts/model_forward_smoke.py` and avoid image preprocessing.
- If testing feature extraction without OpenCV is impossible in the current environment, report that preprocessing could not be validated and keep model-only construction as a separate verified fact.

## Source-only package import failures

Symptoms:

- `ModuleNotFoundError: No module named 'fastreid'`
- Import succeeds only when running from the repository root.
- Distribution metadata for `fastreid` or `fast-reid` is missing.

Resolution:

- Use scripts with `--repo-root /path/to/fastreid-source` so they insert the source checkout into `sys.path` for that process.
- Alternatively, configure the Python environment's import path to include the source checkout.
- Do not depend on editable package metadata: this source snapshot is not a standard installable Python distribution.

## Python-version compatibility

Symptom:

- Import errors involving `collections.Mapping` or similar compatibility aliases on modern Python versions.

Resolution:

- Prefer Python 3.9 for this FastReID version unless the source has been patched for newer Python compatibility.
- If a user must use a newer Python, patch deprecated `collections` imports to `collections.abc` in a controlled branch and rerun import/model smokes.

## Dry-run prevents pretrain download but output quality is random

A dry-run with no checkpoint and no pretrained backbone proves only that the API, config, preprocessing, and forward tensor path work. It does not prove identity retrieval quality. For quality-sensitive inference, require a matching config, a matching local checkpoint, and a dataset/query-gallery validation workflow routed through training-and-evaluation.
