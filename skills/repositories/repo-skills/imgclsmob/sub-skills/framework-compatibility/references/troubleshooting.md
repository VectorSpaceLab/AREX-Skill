# Framework compatibility troubleshooting

Use these recipes to classify a compatibility failure before changing
packages. The probe is read-only and no-network. Do not install a mixed modern
and legacy framework set, download weights, fetch datasets, start training, or
run conversion tests while diagnosing availability.

Every result must retain the requested framework label. A CPU Gluon or
PyTorch/pytorchcv fallback can answer a narrowly scoped shape/forward question,
but it does **not** turn a TF1, TF2, Keras, or Chainer result into a verified
result for that framework.

## Probe says a distribution is present but its import is missing

**Symptom:** `importlib.metadata.version(...)` prints a version, but
`find_spec(...)` is missing or the requested import raises
`ModuleNotFoundError`.

**Cause:** the distribution and the active Python interpreter/environment do
not match, or an optional dependency was only partially installed. Distribution
and import names are not always identical: `keras-mxnet` is a distribution,
while its model route is `kerascv` and its runtime import is `keras` plus the
MXNet backend; `chainercv2` is the distribution and `chainercv2` is the public
provider import, while train/eval helpers may also use `chainercv`.

**Recovery:** rerun the probe with the exact interpreter that will execute the
entrypoint, record both results, and classify the request as
**blocked-optional-backend** until the environment is repaired and separately
verified. Do not infer compatibility from metadata alone. For a no-network
shape/forward check, route to the CPU Gluon or PyTorch/pytorchcv fallback in
[model-inference](../../model-inference/SKILL.md).

## TensorFlow 2 request cannot import TensorFlow

**Symptom:** a request names `tf2cv`, `train_tf2.py`, `eval_tf2.py`,
`examples/demo_tf2.py`, or TF2-to-TFLite conversion, but `import tensorflow`
fails or `tensorflow` is absent.

**Cause:** `tf2cv==0.0.18` exposes `tf2cv.model_provider.get_model`, but its
model code and `tensorflow2.utils.prepare_model(...)` import TensorFlow. The
documented runtime prerequisite is `tensorflow>=2.0.0`; the package metadata
itself declares only `numpy` and `requests`.

**Recovery:** report: “TF2 is bounded-unverified here; the TensorFlow runtime
is missing or was not live-verified.” Mark the requested operation
**blocked-optional-backend** when the runtime is absent. Ask for a dedicated
TF2 environment decision before proceeding. If the user only needs a local
CPU/no-network forward, use `pretrained=False`, an empty checkpoint, and the
verified CPU Gluon or PyTorch fallback. Do not use `examples/demo_tf2.py` as a
fallback: it requires an image and always requests `pretrained=True`.

## TensorFlow 2 checkpoint, build, or input-shape mismatch

**Symptom:** `tensorflow2.utils.prepare_model` rejects a checkpoint,
`load_weights` reports missing or incompatible shapes, or TF2/TFLite model
construction fails after changing `in_size`, `batch_size`, or data format.

**Cause:** the selected model name, local checkpoint, `net_extra_kwargs`
(especially input size), batch dimension, and channel layout do not describe
the same model. A non-empty `pretrained_model_file_path` must be a local file;
`use_pretrained=True` can request automatic weights. TFLite helper invocation
without an explicit input also requests pretrained weights.

**Recovery:** first use `pretrained=False` and an empty checkpoint to separate
model construction from loading. Confirm the model name, input shape, and
`channels_first`/`channels_last` contract. Use `load_ignore_extra=True` only
when intentionally accepting skipped or mismatched layers, and report the
result as partial. Keep conversion and TFLite validation behind the conversion
sub-skill's backend gate. If TF2 remains unavailable, route only a narrow CPU
forward check to the verified fallback and retain the TF2 unverified label.

## Legacy TensorFlow 1 / Tensorpack is confused with TF2

**Symptom:** `tensorflowcv` or `tensorflow_.utils.prepare_model` fails with
`tf.placeholder`, graph/session, `tf.contrib`, or Tensorpack errors; or a user
proposes upgrading the environment to TensorFlow 2 to fix a TF1 request.

**Cause:** the requested surface is **legacy TensorFlow 1 / Tensorpack (TF1)**,
not TF2. Its package is `tensorflowcv==0.0.38`, with documented
`tensorflow>=1.11.0`; this expression is not a modern compatibility pin. The
plain route imports `tensorflowcv.model_provider.get_model` and uses graph
placeholders plus a TensorFlow session. The Tensorpack route uses
`tensorflow_.utils_tp.prepare_model(..., data_format=...)` and has a distinct
execution contract.

**Recovery:** do not upgrade to TF2 and report success. Preserve the **legacy
TF1** label, classify the operation **blocked-optional-backend** until a
matching isolated TF1/Tensorpack environment is supplied and verified, and
keep `channels_first` versus `channels_last` explicit. For an equivalent but
not TF1-valid CPU shape/forward check, offer the verified Gluon or PyTorch
fallback and say that it does not validate TF1.

## Tensorpack evaluation fails despite `--num-gpus=0`

**Symptom:** `eval_tf.py --num-gpus=0` still fails while constructing a
predictor, staging input, or device placement.

**Cause:** the Tensorpack evaluator uses `StagingInput(..., device="/gpu:0")`
in its predictor path. A zero GPU argument is therefore not evidence of a
CPU-safe Tensorpack evaluation. The plain graph helper and Tensorpack helper
also use different preparation/data-format paths.

**Recovery:** stop the evaluation rather than silently substituting TF2. Keep
the result **legacy TF1 bounded-unverified**, request a dedicated compatible
TensorFlow/Tensorpack environment, and record the device and data-format
contract. If the goal is only a no-network model forward, route to the verified
CPU fallback; route data, metrics, and epoch semantics to
[training-evaluation](../../training-evaluation/SKILL.md).

## Keras provider imports but compilation or tensor layout fails

**Symptom:** `kerascv.model_provider.get_model(...)` constructs a model but
compilation fails, MXNet context arguments are rejected, or dimensions appear
in the wrong channel order.

**Cause:** `kerascv==0.0.40` declares only `h5py`. The documented alternatives
are MXNet (`mxnet>=1.2.1` plus the `keras-mxnet` distribution) or a TensorFlow
backend. The `keras` module alone does not identify the selected backend. The
Keras configuration and model/data layout must agree; the MXNet guidance
prefers `channels_first`.

**Recovery:** record the selected Keras backend and data format, then use one
consistent backend. The project helper
`keras_.utils.backend_agnostic_compile(...)` selects MXNet `cpu()` when the GPU
count is zero and `gpu(i)` otherwise, but neither branch is live-verified here.
Classify the operation **bounded-unverified** until exercised in its matching
environment. For a narrow local forward request, offer the verified CPU
fallback and explicitly state it is not Keras validation.

## Keras record-file or resume failure

**Symptom:** `train_ke.py` or `eval_ke.py` cannot open a record/index file, or
`--resume` fails while loading weights.

**Cause:** these commands use MXNet record files and require the four-file
contract `--rec-train`, `--rec-train-idx`, `--rec-val`, and `--rec-val-idx`.
`--resume` is a model file loaded by `net.load_weights`; training's
`--resume-state` is optimizer state. A Keras HDF5 file is not automatically a
TF1, TF2, or Chainer checkpoint.

**Recovery:** check that each file is locally present and that the selected
Keras backend can read it before starting a run. Do not enable
`--use-pretrained` for an offline diagnostic. Stop at the file-contract error,
route dataset/metric/epoch questions to
[training-evaluation](../../training-evaluation/SKILL.md), and route format
translation to [conversion](../../conversion/SKILL.md). Use the verified CPU
fallback only for a deliberately narrower model-forward check.

## Chainer or Chainer/CuPy device failure

**Symptom:** `chainercv2.model_provider.get_model(...)` imports but GPU use
fails; `num_gpus > 0` fails in `net.to_gpu()`; or the project utility fails
before model creation with a Chainer/CuPy import or device error.

**Cause:** `chainercv2==0.0.62` declares `requests` and `chainer>=5.0.0`.
Train/eval paths also use `chainercv`, and GPU paths require a matching CuPy
build. The provider route is `chainercv2.model_provider.get_model`; the
project helper imports `cupy` at module load and
`prepare_ch_context(num_gpus)` selects a CuPy device for a positive count.
Thus even a nominal CPU helper path can be blocked by a missing CuPy import;
that is an environment fact, not proof that Chainer CPU execution works.

**Recovery:** record Chainer, ChainerCV, and CuPy distributions independently.
Use `num_gpus=0` only as a bounded CPU configuration after the imports are
available; never claim it was verified here. For GPU failure, stop and request
a matching Chainer/CuPy environment. For a checkpoint failure, verify that the
file is Chainer NPZ before retrying. Otherwise route a narrow no-network
forward check to the verified CPU fallback.

## Chainer checkpoint cannot load

**Symptom:** `load_npz` rejects `--resume`, reports missing links, or fails on
a Keras HDF5/TF checkpoint.

**Cause:** `chainer_.utils.prepare_model(...)` loads a Chainer NPZ into the
selected model. TensorFlow checkpoints and Keras HDF5 files use different
serialization and parameter naming contracts.

**Recovery:** stop loading, verify the local file type and model name, and do
not rename the extension as a conversion. Route checkpoint translation to
[conversion](../../conversion/SKILL.md). Keep the Chainer result
**bounded-unverified**, even if package imports succeed, because Chainer was
not live-verified in this production run. A fallback CPU forward is allowed
only if the user accepts that it is not Chainer evidence.

## CUDA requested on a CPU or unverified wheel

**Symptom:** a command requests `--num-gpus > 0`, a CUDA-specific package, or a
GPU conversion test; the host has a visible GPU but the operation fails or
selects an unexpected device.

**Cause:** a visible GPU does not prove that the installed framework wheel,
CUDA runtime, CuPy/MXNet build, and driver are a compatible set. Optional
TensorFlow, legacy TF1/Tensorpack, Keras-MXNet, and Chainer GPU paths are all
unverified here.

**Recovery:** classify the GPU operation as **blocked-optional-backend** and
request a matching backend environment. You may suggest `--num-gpus=0` only
for a bounded CPU/API check; do not present that check as equivalent GPU
support or as verification of the original framework. Route conversion-specific
GPU gates to [conversion](../../conversion/SKILL.md). If the requirement is only
model shape/forward, use the verified CPU fallback.

## Pretrained flag unexpectedly accesses the network

**Symptom:** model construction or a demo contacts a weight host, hangs while
loading weights, or fails due to unavailable network access.

**Cause:** `pretrained=True`, `--use-pretrained`, or a preparation helper with
a non-empty automatic-weight path requests weights. `examples/demo_tf2.py`
always requests pretrained weights, and TF2-to-TFLite conversion requests them
when its explicit input/checkpoint route is not supplied.

**Recovery:** terminate the network-dependent operation. For an offline smoke
use `pretrained=False`, an empty checkpoint path, a small synthetic input, and
the verified CPU Gluon or PyTorch/pytorchcv route. Never describe a test that
used automatic weights as no-network evidence. Keep optional backend status
unverified unless that exact backend was separately exercised.

## Unsupported model name

**Symptom:** a provider raises `ValueError: Unsupported model: ...`.

**Cause:** each provider lower-cases the name and searches its own registry.
A name valid in Gluon or PyTorch is not guaranteed to be registered in TF1,
TF2, Keras, or Chainer.

**Recovery:** inspect the model list for the requested provider, retry only with
a registered name, and retain the requested framework label. If the requested
backend is unavailable, do not silently use another provider; offer the
verified CPU fallback only for an explicitly equivalent, narrower check and
route model/dataset execution to the appropriate downstream sub-skill.
