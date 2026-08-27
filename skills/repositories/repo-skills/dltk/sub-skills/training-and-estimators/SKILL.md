---
name: training-and-estimators
description: "Compose DLTK TensorFlow 1.x Readers, model functions,
  EstimatorSpec objects, training and evaluation loops, checkpointed model
  directories, exports, and the legacy monitored-session GAN workflow."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training and estimators

Use this route when a task asks how to train a DLTK network, write a
`model_fn`, connect a `Reader` to `tf.estimator.Estimator`, evaluate or resume
a run, export a SavedModel, inspect TensorBoard events, or adapt one of the
six legacy applications. It is an operating guide for DLTK 0.2.1, not a
modern-TensorFlow migration guide.

## Compatibility gate

DLTK 0.2.1 is a TensorFlow 1.x graph-mode package. A known compatible
reference configuration is Python 3.7 with TensorFlow 1.15.0; this is a
portable compatibility recommendation, not a private inspection environment
or a universal requirement. Other TensorFlow 1.x configurations may work only
when the required APIs and package dependencies are present. The package and
its examples use APIs such as `tf.Session`, `tf.layers`, `tf.contrib`, and
`tf.estimator`. Stop before training when the backend is TensorFlow 2.x or
those APIs are absent; do not silently rewrite the application with Keras or
`tf.data` v2, and do not claim TensorFlow 2.x support.

The public README recommends TensorFlow >=1.4.0, while the legacy
`requirements.txt` pins `tensorflow-gpu==1.3.0`. Those source declarations are
historical and contradictory; neither one establishes modern TensorFlow 2.x
support. Resolve the version choice deliberately, using the reference
configuration above as a known-compatible starting point rather than guessing.

Run a smallest import probe before touching data:

```bash
python - <<'PY'
import tensorflow as tf
from dltk.version import __version__
assert __version__ == '0.2.1'
required = ('Session', 'layers', 'contrib', 'estimator')
missing = [name for name in required if not hasattr(tf, name)]
if missing or not tf.__version__.startswith('1.'):
    raise SystemExit('DLTK training requires TensorFlow 1.x; missing: %s' % missing)
print('tensorflow=%s dltk=%s' % (tf.__version__, __version__))
PY
```

For a bounded, data-free integration check, run
`scripts/tiny_estimator_smoke.py --help` and then
`scripts/tiny_estimator_smoke.py`. The helper creates a temporary model
directory owned by that invocation, performs one-step synthetic
Reader-to-Estimator training and evaluation, resumes in the same directory,
and validates a SavedModel export. It never downloads data and rejects its
destructive `--restart` compatibility flag.

## Route the task

- Reader signatures, nested output dtypes/shapes, patch extraction, or serving
  input construction belong with [data-pipelines](../data-pipelines/SKILL.md).
- Network choice, output dictionaries, rank-5 inputs, and DLTK losses/metrics
  belong with [model-building](../model-building/SKILL.md).
- SavedModel prediction, sliding windows, crop averaging, and NIfTI output
  belong with [inference-and-deployment](../inference-and-deployment/SKILL.md).
- This route owns the composition between those contracts: `Reader -> input_fn
  and initializer hook -> model_fn -> EstimatorSpec -> train/evaluate/export`.

Open the linked references in this order:

1. [workflows.md](references/workflows.md) for the graph contract and safe
   train/evaluate/resume/export sequence.
2. [application-recipes.md](references/application-recipes.md) to select one
   of the six example shapes and objectives.
3. [cli-reference.md](references/cli-reference.md) for exact legacy flags.
4. [troubleshooting.md](references/troubleshooting.md) when a gate fails.

## Non-negotiable safety rules

- Treat application scripts as data-bound demonstrations, not production
  trainers or tuned high-performance baselines. They expect downloaded IXI or
  registered MRBrainS data, SimpleITK-readable layouts, large historical step
  counts, and sometimes GPU memory. Do not start a full run merely to test an
  import, and do not promise their plotted accuracy or loss.
- Existing `model_dir` means resume when the graph, parameter shapes, and
  feature contract are compatible. Preserve it until its checkpoints and
  events have been inspected. The original examples expose `--restart` and
  implement it with shell-based recursive deletion; reject that behavior. Use
  a new model directory for an intentional fresh run, or perform a separately
  approved, reversible archive/rename outside the training code. Never tell an
  agent to use an unreviewed recursive-delete command.
- Keep training bounded while validating: one or a few steps, a tiny fixture,
  a temporary directory, and explicit export checks. Dataset downloads,
  credential-gated data, pretrained archives, and full example training are
  excluded from this route's smoke checks.
- Seed NumPy and TensorFlow when comparing a smoke run. Seeded toy behavior is
  a contract check, not evidence of medical-model quality.

## Minimal contract

A custom function has the exact shape
`model_fn(features, labels, mode, params)` and returns a
`tf.estimator.EstimatorSpec`. Build the model output dictionary first, return a
prediction-only spec for `ModeKeys.PREDICT`, and only then build loss,
optimizer, metrics, and summaries for TRAIN/EVAL. `params` is passed by the
Estimator and is the right place for learning rate, class count, or an
upsampling factor.

`Reader.get_inputs(...)` returns both an input function and an initializer
hook. Pass the matching hook to every `Estimator.train` and `Estimator.evaluate`
call. The Reader's `dtypes` and `example_shapes` must exactly match every
nested value yielded by `read_fn`; labels are not inferred from the model.
Common feature tensors are rank 5 `[batch, depth, height, width, channels]`.
Classification/regression labels are normally `[batch, 1]`; segmentation
labels are integer `[batch, depth, height, width]`; feature-only CAE and
super-resolution recipes pass `labels=None`.

Use the matching objective: floating-point logits and labels for regression
MSE; integer class ids converted with `tf.one_hot` for classification softmax
cross-entropy; integer voxel ids with sparse softmax cross-entropy for
segmentation; and the input feature tensor itself as the target for a
feature-only reconstruction or super-resolution model. When a network uses
batch normalization, put `tf.get_collection(tf.GraphKeys.UPDATE_OPS)` in
control dependencies around `optimizer.minimize`, or moving averages will not
be updated during training. Preserve the model output keys (`logits`, `y_`,
`y_prob`, or `x_`) used by the selected loss and downstream predictor.

For export, return a named `PredictOutput` and use a serving receiver whose
feature placeholder shape is `[None] + per-example-feature-shape`. Do not
invent a label input for prediction. Validate that the exported receiver,
network rank, channel count, and any divisibility requirements agree before
calling deployment code.

A safe application invocation is intentionally preceded by `--help`, an
import/API probe, a caller-validated CSV and data-layout check, and a new or
explicitly approved model directory. See the references for the six exact
flag sets and objective-specific details.
