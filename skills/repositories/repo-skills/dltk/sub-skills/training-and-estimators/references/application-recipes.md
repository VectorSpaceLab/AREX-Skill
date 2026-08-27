# Application recipes

These recipes distill the six public DLTK 0.2.1 application examples. They
are examples, data-bound, and not tuned for high performance. They are useful
for choosing a model function and checking an input contract; they are not a
benchmark, a production medical pipeline, or a guarantee that a downloaded
checkpoint will restore in every environment.

Every application parses a CSV with pandas, builds one or two DLTK `Reader`
input functions, creates an Estimator (except the GAN), periodically trains
and evaluates, writes checkpoints/events under `model_path`, and generally
exports at the end. DLTK 0.2.1 targets TensorFlow 1.x graph mode; Python
3.7/TensorFlow 1.15.0 is a known compatible reference configuration, not a
private environment or a universal requirement. Before any non-tiny run,
inspect the caller-supplied entry point's `--help`, confirm the selected
runtime exposes the required TF1 APIs, and validate the CSV, SimpleITK-readable
files, patch shapes, free disk, and model directory.

## Age regression with 3-D ResNet

**Purpose.** Predict a continuous age value from one-channel T1-weighted
images. The model calls `resnet_3d` with `NUM_CLASSES=1`, two residual units,
filters `(16, 32, 64, 128, 256)`, and strides that downsample each later scale.
It uses an L2 regularizer, Adam with learning rate `0.001` and `epsilon=1e-5`,
MSE loss, and RMSE/MAE evaluation metrics.

**Contract.** The application Reader normalizes a single image, expands a
channel axis, optionally flips during TRAIN, and extracts examples with
`example_size=[64, 96, 96]`. Its `features['x']` is float32 with per-example
shape `[64, 96, 96, 1]`; `labels['y']` is float32 `[1]`. The training Reader
is declared for batch size 8 and a shuffle cache of 32. A compatible custom
reader must yield the declared float dtype, not a Python scalar or an integer.

**Loop/export.** It splits the first 150 CSV rows for training and the
remaining rows for validation, trains in 100-step rounds, evaluates for 5
steps, and uses a `SummaryAtEndHook` under `model_path/eval`. Its export
receiver permits dynamic per-example spatial dimensions with one channel;
validate any downstream crop or window dimensions before using that export.
The default application budget is 50,000 steps, so it is not an import smoke.

## Sex classification with 3-D ResNet

**Purpose.** Predict two classes from one-channel T1-weighted images with the
same broad ResNet family and filter schedule as regression, but
`NUM_CLASSES=2`, an L2 regularizer of `1e-3`, and Adam learning rate `0.001`.
The model reshapes integer class ids through `tf.one_hot`, applies softmax
cross-entropy, and reports accuracy and precision from `y_` and the labels.

**Contract.** The application Reader normalizes and optionally flips a
single-channel image, extracts `[64, 96, 96, 1]` examples, and maps source
class values 1/2 to 0/1. The training `Reader` declares `labels['y']` as
`tf.int32` with shape `[1]`, but the historical Reader implementation yields
that label as float32. Treat this as a real failure mode: correct the reader
to yield int32 before using it, or make the dtypes and loss deliberately
consistent. Do not hide the mismatch with an implicit cast.

**Loop/export.** The first 150 rows are training and the rest validation;
training rounds are 100 steps and evaluation is capped at 5 steps. The
receiver has dynamic spatial dimensions and one channel. The legacy default
is 50,000 steps and the source application is not tuned for high performance.

## MRBrainS tissue segmentation with residual U-Net

**Purpose.** Segment nine tissue classes from three MR sequences. The model
uses `residual_unet_3d`, two residual units, filters `(16, 32, 64, 128)`,
strides `((1,1,1),(1,2,2),(1,2,2),(1,2,2))`, an L2 regularizer of `1e-4`, and
Momentum with learning rate `0.001` and momentum `0.9`. It uses sparse voxel
cross-entropy and logs per-class Dice tensors through a Python callback.

**Contract.** A reader stacks normalized T1, T1 inversion-recovery, and T2
FLAIR channels. With extraction enabled, the source shape is
`features['x']=[4,128,128,3]` float32 and `labels['y']=[4,128,128]` int32 for
nine classes. Labels must be integer ids in the logits' class range; one-hot
labels are not accepted by the sparse loss. The application uses class-
balanced patch extraction and a small five-subject split, but the data is
registration-gated and not included in this skill.

**Loop/export.** The example trains in 100-step rounds and evaluates one step,
with a 50,000-step default. Its serving receiver uses the example shape.
Check that the exported logits and `y_` spatial dimensions match the sliding-
window/deployment route before inference. A CPU graph check is reasonable;
full 3-D training is expensive and data-bound.

## Feature-only convolutional autoencoder

**Purpose.** Learn a reconstruction representation from three-channel T1,
T2, and PD images. The model calls `convolutional_autoencoder_3d`, uses
filters `(16,32,64,128,256)`, two convolutions per scale, a 1024-unit hidden
layer, and Adam learning rate `0.01`. It minimizes MSE between `features['x']`
and the reconstructed output `x_`; there is no label tensor.

**Contract.** The feature-only Reader stacks three whitened channels and
extracts per-example `[1,224,224,3]` float32 patches. `labels` is absent, so a
custom `model_fn` must not dereference `labels['y']`. This is a common reason
to route the request here rather than treating every Estimator as a
supervised classifier.

**Loop/export.** The source splits 100 subjects from the remainder, uses
100-step training rounds and 10-step evaluation only when requested, and
exports the Reader feature shape. Its 100,000-step default, three-file
SimpleITK input, and high-resolution network make it data-bound. Latent
`hidden_units` can be exposed in prediction, but the exported output and
consumer must agree on names.

## Artificial super-resolution

**Purpose.** Reconstruct a high-resolution feature from an artificially
low-resolution version. During TRAIN/EVAL the example applies
`tf.layers.average_pooling3d` with a kernel twice each factor and strides
`[4,4,4]`, compares a linear upsample baseline, then calls
`simple_super_resolution_3d`. It minimizes MSE between the original feature
and output `x_` with Adam learning rate `0.01`.

**Contract.** The Reader supplies one-channel whitened features with
per-example shape `[32,128,128,1]`; there are no labels. TRAIN/EVAL input is
interpreted as the high-resolution target from which the synthetic low-
resolution tensor is made. PREDICT input is expected to be low-resolution,
not the same tensor shape used by training. Make this mode-dependent contract
explicit in a serving client.

**Caveat.** The application README explicitly says the average-pooling
experiment is only a setup demonstration and should be replaced by a proper
downsampling strategy in practice. It is not evidence of real super-
resolution quality. The default is 250,000 steps with 100-step rounds and
2-step evaluation; only graph/shape checks should be automatic.

## Custom 3-D LSGAN / DCGAN-like loop

**Purpose.** Generate 3-D image slices from a noise feature and train a
separate discriminator. This is not an Estimator workflow: it uses explicit
variable scopes, two optimizers, and `tf.train.MonitoredTrainingSession` for
checkpointing and summaries. The Reader exposes a noise feature shaped
`[1,1,1,100]` and real image labels shaped `[4,64,64,1]` in the source example.

**Graph contract.** Build the generator under `generator`; build the fake
discriminator under `discriminator`; reuse that scope for real data. The
least-squares discriminator targets are ones for real and zeros for fake; the
generator target is ones. Select discriminator variables and generator
variables by their scopes, then minimize each loss with its own Adam optimizer
(learning rate `0.001`, beta-like second argument `0.5`, epsilon `1e-5`).
Create a global step, increment it explicitly, and pass the Reader
initializer hook to the monitored session.

**Safety.** The source default is 35,000 steps with 8-example batches and
100-step summaries. The loop conditionally skips one side when its loss is
much better, so loss scheduling is part of the example behavior. Keep this
recipe reference-only unless the caller explicitly wants a bounded graph
check. Do not wrap it in an Estimator merely to make the API uniform, and do
not use its legacy recursive-delete restart path.

## Shared application limitations

The examples read file paths from caller CSVs, assume historical pandas APIs,
normalize or augment in Python, and may return metadata that the Reader
strips. They use hard-coded summary display sizes and large default step
counts. A help probe proves only that the parser and compatible imports load;
it proves neither data completeness nor model quality. For reader path,
resampling, and label synchronization details use the data-pipelines route;
for model signatures use model-building; for predictor/crop/stitching and
NIfTI metadata use inference-and-deployment.
