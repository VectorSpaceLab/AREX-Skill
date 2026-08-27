# Estimator workflows

This reference describes the source-faithful TensorFlow 1.x composition used
by DLTK 0.2.1. It deliberately uses synthetic examples for bounded checks; the
medical application readers and CSVs remain caller-supplied inputs.

## 1. Establish the contracts

A DLTK `Reader` is constructed with a Python generator function and a nested
`dtypes` structure. The generator has the public signature:

```python
def read_fn(file_references, mode, params=None):
    yield {'features': {'x': feature_array},
           'labels': {'y': target_array}}
```

`labels` may be omitted for feature-only examples. A prediction reader may
return extra metadata, but the Reader removes keys not listed in `dtypes`.
Do not rely on metadata being available to `model_fn`; use a separate
prediction path if an image id or SimpleITK object must be retained.

Create matching shape metadata and input functions:

```python
reader = Reader(
    read_fn,
    {'features': {'x': tf.float32}, 'labels': {'y': tf.int32}})
input_fn, init_hook = reader.get_inputs(
    file_references=references,
    mode=tf.estimator.ModeKeys.TRAIN,
    example_shapes={
        'features': {'x': [depth, height, width, channels]},
        'labels': {'y': [depth, height, width]},
    },
    batch_size=2,
    shuffle_cache_size=2,
    params=reader_params)
```

The concrete shape list is per yielded example; batching adds the leading
batch dimension. The Reader repeats and shuffles its dataset, so bounded
`steps=` is required for a smoke or validation run. Its initializer hook must
run after the session is created, which is why it belongs in both train and
evaluate hooks.

The tutorial's synthetic circles are 2-D masks represented with a singleton
depth-like axis: feature samples are `[1, height, width, 1]` and mask samples
are `[1, height, width]`. This is useful for a small graph check, but DLTK's
3-D network functions still require a batched rank-5 tensor.

## 2. Build `model_fn` in mode order

Use this order so prediction does not accidentally consume labels or build a
training optimizer:

1. Read `features['x']` and call a selected DLTK network with `mode=mode`.
2. If `mode == tf.estimator.ModeKeys.PREDICT`, return
   `EstimatorSpec(mode=mode, predictions=outputs,
   export_outputs={'out': tf.estimator.export.PredictOutput(outputs)})`.
3. Construct the objective with the exact label dtype and rank.
4. Get `tf.train.get_global_step()`, select an optimizer, collect
   `tf.GraphKeys.UPDATE_OPS`, and minimize under their control dependency.
5. Add only shape-valid summaries and EVAL metrics.
6. Return one `EstimatorSpec` containing `predictions`, `loss`, `train_op`, and
   optional `eval_metric_ops`.

The application model functions use DLTK output dictionaries as predictions.
The recurring keys are:

| Recipe | Main output | Target and objective |
|---|---|---|
| Regression | `logits` with final width 1 | float `[B, 1]`, mean squared error |
| Classification | `logits`, `y_prob`, `y_` | integer ids, one-hot softmax cross-entropy |
| Segmentation | voxel `logits`, `y_prob`, `y_` | integer voxel ids, sparse softmax cross-entropy |
| CAE | reconstructed `x_`, latent `hidden_units` | `features['x']`, mean squared error |
| Super-resolution | reconstructed `x_` | high-resolution `features['x']`, mean squared error |
| LSGAN | discriminator logits | separate real/fake least-squares losses; not an Estimator |

The regression application uses `tf.losses.mean_squared_error` and RMSE/MAE
metrics. The classification application reshapes one-hot labels to `[-1,
NUM_CLASSES]` before softmax cross-entropy and logs accuracy/precision. The
segmentation application reduces `tf.nn.sparse_softmax_cross_entropy_with_logits`
over voxels and logs per-class Dice values through a `tf.py_func`; that Dice
summary is not an Estimator `eval_metric_ops` entry. Match these semantics
rather than comparing incompatible label encodings.

## 3. Reader-to-Estimator train/evaluate loop

The six applications follow the same long-running structure:

```python
estimator = tf.estimator.Estimator(
    model_fn=model_fn,
    model_dir=model_dir,
    params={'learning_rate': learning_rate},
    config=tf.estimator.RunConfig())

for _ in range(number_of_rounds):
    estimator.train(
        input_fn=train_input_fn,
        hooks=[train_qinit_hook, step_counter_hook],
        steps=eval_every_n_steps)
    if run_validation:
        result = estimator.evaluate(
            input_fn=val_input_fn,
            hooks=[val_qinit_hook, summary_at_end_hook],
            steps=eval_steps)
        print(result['global_step'], result['loss'])
```

For a first run, replace the application step count with one or two steps and
use a synthetic or already validated fixture. `EVAL_STEPS` is a cap, not a
promise that the validation set contains that many independent examples. An
input function that repeats forever must always be bounded by `steps`.

`tf.train.StepCounterHook` writes step-rate information to the model
 directory. The examples use `tf.contrib.training.SummaryAtEndHook` with an
`eval` subdirectory and regular `tf.summary.*` calls in `model_fn`. A standard
monitoring command is:

```bash
tensorboard --logdir MODEL_DIR
```

Use a model directory that contains only the run being inspected, and compare
training and evaluation event series by their global step. Image summaries
must be rank 4 `[batch, height, width, channels]`; application examples slice
one depth plane and reshape it to a hard-coded display size. If you change a
patch size, change or remove those display summaries before training.

## 4. Checkpoints, resume, and safe fresh runs

An Estimator with `model_dir` creates checkpoints and a global step. A second
`train` call on the same Estimator or a newly constructed Estimator with the
same compatible `model_dir` resumes from the latest checkpoint. A changed
network scope, tensor shape, optimizer slot shape, class count, or feature
contract can make that directory incompatible; do not force the restore.

Validate resume without destruction:

1. Train one bounded step in a new temporary or explicitly empty directory.
2. Read or evaluate `global_step`.
3. Train one more bounded step against that same directory.
4. Confirm the step increased by exactly the requested number.
5. Evaluate and export from the resumed graph.

A fresh run gets a caller-chosen new directory after checking that it does
not already contain checkpoints. Do not use the legacy application `--restart`
implementation, which shells out to recursive deletion. If an old run must be
retired, preserve it by an approved archive/rename operation and record the
new directory; the training command itself should never delete arbitrary
paths.

## 5. SavedModel export and serving shapes

The Reader's `serving_input_receiver_fn` creates feature placeholders with a
leading batch dimension. For a per-example feature shape `[64, 96, 96, 1]`,
the receiver shape is `[None, 64, 96, 96, 1]`. The application regression and
classification examples instead use dynamic spatial dimensions with a fixed
channel count. CAE, segmentation, and super-resolution examples pass their
training example shape. The receiver function only creates feature
placeholders from the Reader's feature dtypes; labels are training/evaluation
inputs, not required prediction inputs.

The export pattern is:

```python
export_dir = estimator.export_savedmodel(
    export_dir_base=model_dir,
    serving_input_receiver_fn=reader.serving_input_receiver_fn(
        {'features': {'x': [depth, height, width, channels]},
         'labels': {'y': label_shape}}))
```

The label entry is harmless to this legacy Reader helper but is not an input
that should be sent to prediction. Validate that `export_dir` exists and
contains `saved_model.pb`, that the feature receiver has the expected rank and
channel count, and that the prediction output names match deployment code.
Dynamic spatial receivers still need dimensions compatible with convolutional
strides and any downstream sliding-window assumptions.

## 6. Custom monitored-session LSGAN path

The DCGAN application is intentionally not an Estimator. It builds a generator
under a `generator` variable scope, a discriminator for fake data under
`discriminator`, then reuses that discriminator scope for real data. It uses
least-squares losses: real target ones, fake target zeros, and generator target
ones. Separate Adam optimizers minimize discriminator and generator variables.

It creates a global step and runs a `tf.train.MonitoredTrainingSession` with a
checkpoint directory, summary cadence, and the Reader initializer hook. Each
loop may run discriminator and generator updates conditionally, increments the
step, and fetches losses and pseudo-accuracies. Keep this as reference-only:
it has a long 35,000-step default, large 3-D examples, and the same unsafe
legacy restart option as the Estimator applications. A bounded GAN graph
check must construct scopes and optimizer variable lists without reading IXI
files or entering the full loop.
