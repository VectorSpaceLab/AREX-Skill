# Training troubleshooting

Use these diagnoses before changing a legacy application. Keep the original
model directory and event files until the cause is understood.

## Import and compatibility failures

**Symptoms:** `AttributeError` for `tf.Session`, `tf.layers`, `tf.contrib`, or
`tf.estimator`; `ModuleNotFoundError` for TensorFlow/DLTK; an application
fails before showing `--help`.

**Checks:** run the compatibility probe in the parent skill, print Python and
TensorFlow versions, and confirm the package version is 0.2.1. DLTK's source
uses TensorFlow 1.x graph APIs. Python 3.7/TensorFlow 1.15.0 is a known
compatible reference configuration, not a private environment or a universal
requirement. The public README recommends TensorFlow >=1.4.0, while the legacy
`requirements.txt` pins `tensorflow-gpu==1.3.0`; these declarations conflict,
so do not combine arbitrary packages to satisfy both. TensorFlow 2.x is not
covered by this route.

**Repair:** use a caller-managed TensorFlow 1.x runtime that passes the API
probe, or stop and report the incompatible backend. Do not import
`tensorflow.compat.v1` into a modern rewrite and claim historical TensorFlow
2.x support.

## Reader generator and nested contract errors

**Symptoms:** `Key ... not found in ex`, incompatible dict/list errors,
`TypeError` from `Dataset.from_generator`, an initializer hook that is never
run, or an immediate `OutOfRangeError`.

**Checks:** compare every yielded key and nested container with `Reader.dtypes`
and `example_shapes`. Confirm each per-example array includes no batch axis
that the Reader will add again, and use `steps=` because the Reader repeats
its dataset. Pass the exact `train_qinit_hook` or `val_qinit_hook` to the
matching Estimator call. Use a tiny generator that yields one known example
before trying SimpleITK or random patches.

The historical application Readers may yield metadata such as subject ids or
SimpleITK images; the Reader removes keys not present in its dtype structure.
A prediction reader that yields once and then falls through into training
branches can also produce an unexpected second sample. When adapting a
reader, return/continue after the intended PREDICT yield and verify its
feature-only output.

## Labels have the wrong dtype or rank

**Symptoms:** sparse cross-entropy rejects labels, one-hot encoding creates an
extra dimension, or the dataset generator reports a dtype mismatch.

**Checks and repairs:**

- Regression: yield float32 `labels['y']` shaped `[1]` per example so a batch
  is `[B,1]`; compare it with a `[B,1]` regression logit.
- Classification: normalize source class ids to zero-based integer ids and
  yield int32 `[1]` labels. The historical sex-classification Reader declares
  int32 in the training script but yields float32; fix the yielded dtype or
  explicitly and consistently change the contract before `tf.one_hot`.
- Segmentation: yield int32 voxel ids shaped `[D,H,W]` per example so the batch
  is `[B,D,H,W]`, while logits are `[B,D,H,W,C]`. Never feed one-hot labels to
  the sparse loss without changing the loss and shape contract.
- CAE and super-resolution: labels are intentionally absent; use the feature
  tensor as the reconstruction target and do not index `labels`.

Inspect `tensor.dtype` and `tensor.get_shape()` in graph construction. Fix the
Reader contract at the boundary instead of sprinkling casts into unrelated
metrics.

## Batch normalization and optimizer behavior

**Symptoms:** training runs but moving means/variances do not update, TRAIN
and EVAL behavior diverges unexpectedly, or a model with batch normalization
restores but performs poorly.

DLTK networks call batch normalization with `training=mode ==
ModeKeys.TRAIN`. Collect `tf.get_collection(tf.GraphKeys.UPDATE_OPS)` after
building the network and create the optimizer op under
`tf.control_dependencies(update_ops)`. Keep the global step supplied to
`optimizer.minimize`. In a custom graph, inspect that update ops and optimizer
variables belong to the intended scope; in the GAN, generator and discriminator
updates are intentionally separate.

## Loss/output wiring errors

**Symptoms:** missing `logits`, `y_`, or `x_`; loss shape broadcasts silently;
summary code fails on rank; export has unusable predictions.

Verify the selected network's output dictionary in the model-building route.
Regression consumes one-width `logits`; classification consumes class logits
and uses `y_prob`/`y_`; segmentation consumes voxel logits and `y_`; CAE and
super-resolution consume `x_`. Make output dictionaries the `predictions`
field, but choose only the tensors required by the loss and metrics. Avoid
hard-coded image-summary reshape sizes after changing patch dimensions.

## Model directory and restart hazards

**Symptoms:** restore errors about missing variables, incompatible checkpoint
shapes, global step starts higher than expected, an export directory contains
multiple confusing versions, or a command would delete a directory.

An existing compatible `model_path` resumes. A different architecture,
channel count, class count, optimizer slot, or serving shape may not. Record
the latest checkpoint/global step, compare the model parameters, and choose a
new path for a fresh graph. Reject `--restart` in all historical applications:
the source implementation shells out to recursive deletion and is unsafe for
an agent. Never replace it with an unreviewed recursive-delete command;
preserve the old path and use an approved archive/rename or an unused new
path.

The bundled smoke tests resume by training twice in the same private
TemporaryDirectory and checks a monotonic global step. That is the safe
restart/resume analogue for this skill.

## SavedModel receiver and serving failures

**Symptoms:** export fails because a placeholder has the wrong rank, a
predictor cannot find the input key, labels are required at serving time, or a
network fails when dynamic spatial dimensions are fed.

Use `Reader.serving_input_receiver_fn` with feature shapes only. It adds the
batch dimension itself. For an example shape `[D,H,W,C]`, inspect for
`[None,D,H,W,C]`; do not prepend two batch dimensions. Return a named
`PredictOutput` and preserve the output keys expected by deployment. Labels
belong to TRAIN/EVAL and should not be sent to the prediction receiver.

Dynamic spatial dimensions are not automatically safe: convolutional stride
stacks, transposed convolutions, crop averaging, and sliding windows may need
fixed or divisible dimensions. Start with the exact training shape, validate
one synthetic prediction, then widen dimensions deliberately.

## TensorBoard appears empty or misleading

**Symptoms:** no scalar/image events, evaluation is missing, or curves have
misaligned steps.

Confirm the model directory is the one passed to the Estimator, that the
initializer hook and bounded evaluate call completed, and that summary ops
were built in the relevant mode. The examples use a step counter and an end
summary hook under an `eval` child directory. Run `tensorboard --logdir` on a
dedicated run and inspect both training and evaluation event locations.
Summary images require rank-4 tensors and the historical examples contain
fixed display sizes; remove or update them when using a tiny fixture.

## Data-bound application failure

**Symptoms:** missing NIfTI files, SimpleITK read errors, CSV columns do not
match, registration is required, or a run consumes unexpectedly large memory.

Stop rather than downloading or repairing data implicitly. Confirm the caller
provided the expected IXI demographic CSV or registered MRBrainS folder layout,
all modality files, and a safe patch size. Dataset download/resampling scripts
are outside this route and may perform network access, large writes, and
cleanup. Use the data-pipelines route for a non-destructive reader check.

## GAN-specific failures

The LSGAN example intentionally uses a monitored session instead of an
Estimator. Check `generator` and `discriminator` variable scopes, that the
real discriminator reuses variables, and that each optimizer receives only
its scope's variables. Confirm the Reader initializer hook is included in the
`MonitoredTrainingSession`. Do not interpret discriminator pseudo-accuracy as
an Estimator metric or convert the alternating loop into a single optimizer
without preserving its objective. Keep the 35,000-step data-bound run out of
smoke verification.
