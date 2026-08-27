# Backend compatibility matrix

Use this reference to classify a framework request before selecting an
entrypoint. It distinguishes the **distribution name**, the public import and
provider route, the helper used by this project, and the runtime prerequisites.
A distribution being installed, a module being discoverable, or a CLI printing
help does not prove that a model can be built, loaded, trained, evaluated, or
converted.

## Verification boundary and status labels

The four optional compatibility surfaces in this matrix were **not live
verified in this production run**. Their rows are therefore explicitly
**bounded-unverified**. No claim of working model construction, checkpoint
loading, dataset execution, CUDA use, or conversion may be made from this
matrix alone.

- **verified-core**: the existing CPU Gluon and CPU PyTorch/pytorchcv smoke
  paths are the declared no-network fallback. They do not verify any optional
  framework row below.
- **bounded-unverified**: package/API and entrypoint contracts are documented,
  but the matching runtime was not exercised here.
- **blocked-optional-backend**: the requested operation needs a missing or
  unverified framework, backend, CUDA build, checkpoint, or conversion
  dependency. Stop and request an environment decision rather than silently
  changing frameworks.

## Distribution and runtime matrix

The `tensorflow` version expressions for the TensorFlow rows are documented
prerequisites, not complete compatibility pins. In particular,
`tensorflow>=1.11.0` must not be interpreted as permission to install a modern
TensorFlow release for a legacy TF1/Tensorpack request. Use an isolated,
TF1-compatible environment and verify it separately.

| Surface (use this label) | Source distribution and version | Declared distribution requirements | Documented runtime/prerequisites | Status |
| --- | --- | --- | --- | --- |
| **TensorFlow 2 (TF2)** | `tf2cv==0.0.18` | `numpy`, `requests` | `tensorflow>=2.0.0`; `tensorflow.keras` is used by model code | **bounded-unverified** |
| **Legacy TensorFlow 1 / Tensorpack (TF1)** | `tensorflowcv==0.0.38` | `numpy`, `requests` | a TensorFlow 1-compatible runtime documented as `tensorflow>=1.11.0`; `tensorpack` for Tensorpack train/eval | **bounded-unverified** |
| **Keras (Keras-MXNet or Keras-TensorFlow)** | `kerascv==0.0.40` | `h5py` | either `mxnet>=1.2.1` plus the `keras-mxnet` distribution, or a TensorFlow-backed Keras install; backend and data format must agree | **bounded-unverified** |
| **Chainer** | `chainercv2==0.0.62` | `requests`, `chainer>=5.0.0` | `chainercv` for the train/eval data helpers; a matching CuPy build for GPU use | **bounded-unverified** |
| CPU fallback (not an optional-row claim) | `gluoncv2==0.0.64` | `numpy` | an MXNet runtime; use the documented CPU Gluon path | **verified-core fallback** |

The PyTorch fallback uses the external `pytorchcv` provider. Its provider
version is not declared by this project metadata; do not invent a version
pin. Both fallback routes remain only fallback evidence and are not substitutes
for a requested TF1, TF2, Keras, or Chainer verification.

## Public imports, providers, and preparation helpers

Use the public provider import for model selection. The preparation helper is a
project utility and is not interchangeable across rows. Each provider lower-
cases the model name and raises an unsupported-model error when the name is not
registered for that provider.

| Surface | Public provider/import route | Preparation route | Checkpoint and device semantics |
| --- | --- | --- | --- |
| **TF2** | `from tf2cv.model_provider import get_model`; call `get_model(name, **kwargs)` | `tensorflow2.utils.prepare_model(model_name, use_pretrained, pretrained_model_file_path, net_extra_kwargs=None, load_ignore_extra=False, batch_size=None, use_cuda=True)` | `pretrained=True` may fetch weights. A non-empty local path must be a file; the model is built before `load_weights`. `load_ignore_extra=True` enables name/mismatch skipping and must be reported as partial when used. |
| **Legacy TF1 / Tensorpack** | `from tensorflowcv.model_provider import get_model`; state-dict initialization is also exposed as `init_variables_from_state_dict` | Plain graph route: `tensorflow_.utils.prepare_model(model_name, use_pretrained, pretrained_model_file_path)`. Tensorpack route: `tensorflow_.utils_tp.prepare_model(..., data_format="channels_last")` with `prepare_tf_context(num_gpus, batch_size)` | Plain route builds `tf.placeholder` tensors and uses a TensorFlow session. Tensorpack route wraps a graph for Tensorpack. Keep `channels_first` versus `channels_last` explicit. Do not call TF2 compatibility proof a TF1 result. |
| **Keras** | `from kerascv.model_provider import get_model`; call `get_model(name, **kwargs)` | `keras_.utils.prepare_model(model_name, use_pretrained, pretrained_model_file_path)`; `backend_agnostic_compile(model, loss, optimizer, metrics, num_gpus)` | `net.load_weights` loads a Keras model file. `backend_agnostic_compile` selects MXNet `cpu()`/`gpu(i)` contexts only when Keras reports the `mxnet` backend; otherwise it uses configured Keras behavior. |
| **Chainer** | `from chainercv2.model_provider import get_model`; call `get_model(name, **kwargs)` | `chainer_.utils.prepare_model(model_name, use_pretrained, pretrained_model_file_path, use_gpus=False, net_extra_kwargs=None, num_classes=None, in_channels=None)` | A non-empty checkpoint is loaded with Chainer `load_npz`; `use_gpus=True` calls `net.to_gpu()`. `Predictor` uses no-backprop inference. A Chainer NPZ is not a Keras HDF5 or TensorFlow checkpoint. |

`keras-mxnet` is a distribution name; the model provider remains the
`kerascv` import and the backend is selected by the Keras configuration. Do
not use the presence of the `keras` module alone to infer whether the backend
is TensorFlow or MXNet.

## Entry-point routing

### TensorFlow 2 (TF2)

- `train_tf2.py` requires `--model`; its default dataset is `ImageNet1K` and
  default `--num-gpus` is `0`. It accepts `--use-pretrained`, `--resume`,
  `--resume-state`, `--batch-size`, `--num-epochs`, `--save-dir`, and worker
  controls. It is a training command, not a smoke test.
- `eval_tf2.py` requires `--model` and accepts `--use-pretrained`, `--resume`,
  `--data-subset {val,test}`, `--calc-flops-only`, `--num-gpus`, and
  `--batch-size`. Even FLOPs mode still needs the TF2 model path.
- `examples/demo_tf2.py` requires `--model` and `--image`, defaults to
  `--num-gpus 0`, and always requests `pretrained=True`; it is not an offline
  availability check.
- `examples/convert_tf2_to_tfl.py` accepts `--model`, optional `--input`,
  `--input-shape`, and `--output-dir`. Without `--input` it requests a
  pretrained model. Route TFLite work through the conversion sub-skill.

The helper's `use_cuda=False` branch selects `/cpu:0` at the API level. That
source-level branch does not establish that the installed TensorFlow wheel or
any TF2 model has been verified here.

### Legacy TensorFlow 1 / Tensorpack (TF1)

- `train_tf.py` and `eval_tf.py` use Tensorpack graph/session APIs and accept
  `--data-dir`, `--data-format`, `--model`, `--use-pretrained`, `--resume`,
  `--num-gpus`, `--batch-size`, and worker/logging controls.
- The script diagnostics name TensorFlow variants and `tensorpack`; those names
  are compatibility clues, not portable modern version pins.
- The evaluator's predictor path uses `StagingInput(..., device="/gpu:0")`.
  Consequently, `--num-gpus=0` is not proof of a CPU-safe Tensorpack evaluation.
- The plain `tensorflow_.utils.prepare_model` route uses graph placeholders,
  session-based state-dict initialization, and `channels_first` by default.
  The Tensorpack helper uses `tensorflow_.utils_tp.prepare_model` and can use
  `channels_last`. Keep the format explicit when comparing checkpoints.

A TF1/Tensorpack request must remain labeled **legacy TF1**, even if a user
suggests installing TensorFlow 2. Upgrading the runtime changes the requested
compatibility surface.

### Keras and Keras-MXNet

- `train_ke.py` and `eval_ke.py` use MXNet record files through
  `--rec-train`, `--rec-train-idx`, `--rec-val`, and `--rec-val-idx`. Both
  require `--model` and accept `--use-pretrained`, `--resume`, `--num-gpus`,
  `--batch-size`, and worker controls.
- The documented installation alternatives are MXNet (`mxnet>=1.2.1` plus
  `keras-mxnet`) or TensorFlow-backed Keras. The `kerascv` metadata itself
  declares only `h5py`, so detect the selected backend separately.
- The MXNet guidance prefers `channels_first`; zero GPUs maps to `cpu()` in
  the compile helper and positive counts request `gpu(i)`. Neither branch was
  live-verified here.
- Distinguish `--resume` (model file loaded by `net.load_weights`) from
  training's `--resume-state` (optimizer state). A Keras HDF5 file is not
  automatically a TF1, TF2, or Chainer checkpoint.

### Chainer

- `train_ch.py` and `eval_ch.py` require `--model` and accept `--use-pretrained`,
  `--resume`, `--num-gpus`, and dataset/model-specific arguments. Evaluation
  also accepts `--data-subset {val,test}` and `--calc-flops-only`.
- `chainercv2==0.0.62` declares `chainer>=5.0.0`; train/eval paths additionally
  use `chainercv` and GPU paths need a compatible CuPy distribution.
- `prepare_ch_context(num_gpus)` selects a CuPy device for a positive count.
  Request a GPU only after checking the Chainer/CuPy pair.
- Chainer checkpoints use `load_npz`; do not pass HDF5 or TensorFlow checkpoint
  files. Route format conversion through the conversion sub-skill.

## No-network prerequisite probe

Run a metadata/spec probe before a framework command. It does not import the
large frameworks and does not fetch anything:

```bash
python - <<'PY'
from importlib.metadata import PackageNotFoundError, version
from importlib.util import find_spec

for dist in (
    "tf2cv", "tensorflow", "tensorflowcv", "tensorpack", "kerascv",
    "keras", "keras-mxnet", "chainercv2", "chainer", "chainercv", "cupy",
):
    try:
        value = version(dist)
    except PackageNotFoundError:
        value = "missing"
    print(f"{dist}: {value}")

for module in (
    "tensorflow", "tensorpack", "keras", "mxnet", "chainer", "chainercv", "cupy",
):
    print(f"import {module}: {'available' if find_spec(module) else 'missing'}")
PY
```

Interpret the result narrowly:

1. Record the requested surface, distribution versions, import-spec results,
   provider route, and preparation helper.
2. If a required distribution or import is missing, classify the request as
   **blocked-optional-backend** and ask whether a dedicated environment may be
   prepared. Do not install a broad mixed dependency set.
3. If everything is present, the result is still **bounded-unverified** until a
   separately approved backend smoke or task run succeeds.
4. A positive GPU listing, a CPU wheel, or a successful import does not prove
   CUDA or model compatibility.

## Fallback and escalation

For only a model-shape or CPU inference check, use `pretrained=False`, an empty
checkpoint argument, one small synthetic input, and the verified CPU Gluon or
PyTorch/pytorchcv route in the model-inference sub-skill. This is a fallback
result, not validation of the requested optional framework.

For dataset, resume, metric, or epoch semantics, route to the
training-evaluation sub-skill after recording the compatibility gate. For
checkpoint translation or TF2-to-TFLite work, route to the conversion sub-skill.
A complete compatibility handoff records:

1. requested surface and exact package/import probe result;
2. exact provider and preparation route;
3. check type: help-only, bounded API check, or live verification;
4. CUDA, network, input-shape, data-format, and checkpoint limits; and
5. fallback or dedicated-environment work required next.
