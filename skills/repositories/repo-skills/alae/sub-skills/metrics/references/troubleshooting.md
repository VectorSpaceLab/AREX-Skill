# Metrics troubleshooting

Use this reference after `../scripts/check_metrics_stack.py` or a native metric command reports a blocker. Keep metric execution optional unless the user explicitly accepts the legacy dependency and sample-count cost.

## Do not import metric modules for debugging

Symptom: a harmless-looking `python -c "import metrics.fid"` starts a TensorFlow session or tries to download files.

Cause: `metrics/fid.py`, `metrics/fid_rec.py`, `metrics/ppl.py`, and `metrics/lpips.py` run `dnnlib.tflib.init_tf()` and `download.from_google_drive(..., directory="metrics")` at module import time.

Response:

- Do not import metric modules just to inspect functions or help.
- Read source text or use `../scripts/check_metrics_stack.py`.
- If metric pickle files are missing, resolve them as explicit artifacts rather than relying on import-time downloads.

## TensorFlow 1.x versus 2.x API errors

Common symptoms:

- `AttributeError: module 'tensorflow' has no attribute 'Session'`
- `AttributeError: module 'tensorflow' has no attribute 'python_io'`
- dnnlib errors around graph/session APIs

Cause: ALAE's data and metric stack expects TensorFlow 1.x-style APIs. TensorFlow 2.x without compatibility shims is not enough for the original scripts.

Response:

- Use an isolated legacy environment.
- Prefer a Python version that can install TensorFlow 1.x wheels.
- Verify `tf.Session` and `tf.python_io` with the checker before launching a metric.
- Do not mix this legacy stack into a modern project environment unless the user accepts the risk.

## Missing or incompatible dnnlib

Common symptoms:

- `ModuleNotFoundError: No module named 'dnnlib'`
- `ModuleNotFoundError: No module named 'dnnlib.tflib'`
- errors inside `dnnlib.tflib` during TensorFlow initialization

Cause: The metrics reuse the old StyleGAN TensorFlow helper stack, not a standard modern PyPI-only deep-learning setup.

Response:

- Install the StyleGAN-compatible `dnnlib` wheel in the same environment as TensorFlow.
- Re-run the safe checker and confirm both `dnnlib` and `dnnlib.tflib` import.
- Do not call `dnnlib.tflib.init_tf()` during readiness checks; let the native metric script do that only when the run is approved.

## Missing metric pickle files

Common symptoms:

- `FileNotFoundError: metrics/inception_v3_features.pkl`
- `FileNotFoundError: metrics/vgg16_zhang_perceptual.pkl`
- import-time download attempts or network failures

Cause: The metric scripts expect StyleGAN-derived pickle models in the repository `metrics/` directory.

Response:

- For FID and reconstruction FID, provide `metrics/inception_v3_features.pkl`.
- For PPL and LPIPS, provide `metrics/vgg16_zhang_perceptual.pkl`.
- Use `../scripts/check_metrics_stack.py --repo-root <ALAE-checkout> --config <config>` to verify presence without importing metric modules.
- If network access is required to fetch them, get explicit user approval and keep download handling outside this bundled metrics checker.

## CUDA/cuDNN mismatches

Common symptoms:

- TensorFlow import warnings about missing `libcudart.so.9.0`, `libcudart.so.10.0`, `libcudnn.so.7`, or similar libraries
- TensorFlow sees no GPU even though PyTorch sees CUDA
- crashes during `dnnlib.tflib.init_tf()` or the first `inception.run`/VGG run

Cause: The README metric instructions target an old TensorFlow GPU/CUDA stack. A modern PyTorch CUDA wheel can work for ALAE model code while TensorFlow GPU execution remains unavailable.

Response:

- First check PyTorch CUDA visibility with the safe checker; ALAE model generation still depends on PyTorch CUDA.
- Treat TensorFlow GPU readiness separately. TensorFlow 1.x import success does not prove GPU metric execution.
- If TensorFlow GPU libraries are unavailable, mark metrics optional/unverified rather than claiming full native metric readiness.
- Avoid changing system CUDA libraries for a shared environment unless the user explicitly asks for a dedicated legacy setup.

## Missing config files or wrong `-c` values

Common symptoms:

- `FileNotFoundError` for a config path
- `metrics/lpips.py` fails immediately with default `configs/experiment_celeba.yaml`
- user asks for ablation/separate-model metrics from README names that are not in this checkout

Cause: The launcher accepts config names and paths, but some source defaults and README-listed ablation files are stale for this checkout.

Response:

- Use existing configs such as `ffhq`, `celeba`, `celeba-hq256`, `bedroom`, `mnist`, or `mnist_fc`.
- For LPIPS, pass a valid config explicitly, for example `python metrics/lpips.py -c celeba`, then verify `DATASET.PATH_TEST` and checkpoint readiness.
- Do not recommend separate-model ablation metrics unless the user supplies the missing implementation and config.

## Missing checkpoint or stale `last_checkpoint`

Common symptoms:

- `No checkpoint found. Initializing model from scratch` followed by meaningless metric behavior or later load errors
- `FileNotFoundError` or `torch.load` failure for a path read from `last_checkpoint`
- warnings about missing state dict keys after changing architecture fields

Cause: Metric scripts load model weights from `OUTPUT_DIR/last_checkpoint`. That file must point to a compatible `.pth` checkpoint for the selected config.

Response:

- Use the safe checker to resolve `OUTPUT_DIR`, `last_checkpoint`, and the pointed checkpoint path.
- If the checkpoint is missing, route to root setup/generation for pretrained artifacts or to `../../training/SKILL.md` for trained checkpoint production.
- If architecture fields changed, route to training/checkpoint compatibility guidance before running metrics.

## Missing TFRecords

Common symptoms:

- TFRecord open/read errors from `TFRecordsDataset`
- FID/reconstruction FID cannot compute real activations
- LPIPS cannot read test images

Cause: Native metric scripts use repository dataset configs, not ordinary image folders.

Response:

- FID and reconstruction FID require `DATASET.PATH` records.
- LPIPS requires `DATASET.PATH_TEST` records.
- Dataset conversion, split, and layout validation belong to `../../data-preparation/SKILL.md`.
- Do not start a 10k/50k metric run before the TFRecord pattern and part counts are verified.

## `fid_sep.py` is excluded

Symptoms:

- `ModuleNotFoundError: No module named 'model_separate'`
- missing `configs/experiment_celeba_sep.yaml`
- user asks for separate encoder/discriminator ablation FID

Cause: `metrics/fid_sep.py` depends on files that are absent in this checkout.

Response:

- Mark `fid_sep.py` unsupported/stale for this generated skill.
- Use `metrics/fid.py` for the supported generation FID route.
- If the user provides a different checkout containing the separate-model files, treat that as a refresh or extension task, not as current ALAE metric guidance.

## Long runtime, memory, or disk pressure

Common symptoms:

- multi-hour metric runs
- GPU out-of-memory at default minibatch size
- large TFRecord reads or output logs filling disk

Cause: Native metric scripts use fixed large sample counts: 50k for FID/reconstruction FID/PPL and 10k for LPIPS, with minibatch `16 * torch.cuda.device_count()`.

Response:

- Get explicit approval before running native metrics.
- For readiness, use only the checker.
- If the user asks for a debug/tiny metric run, explain that the repository scripts hard-code sample counts and would require a temporary source edit or external wrapper; do not silently modify the repository from this metrics sub-skill.
