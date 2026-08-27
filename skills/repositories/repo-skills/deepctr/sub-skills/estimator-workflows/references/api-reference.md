# DeepCTR Estimator API Reference

DeepCTR 0.9.4 includes a legacy TensorFlow Estimator surface under `deepctr.estimator`. It is intended for large-scale, TFRecord, Pandas-input, and distributed TensorFlow Estimator workflows when the installed TensorFlow build still exposes top-level `tf.estimator`.

## Package/runtime facts

- Distribution/import name: `deepctr`
- DeepCTR version represented by this skill: `0.9.4`
- Python support advertised by the package: `>=3.7`
- TensorFlow support advertised by the package: TensorFlow `1.15` and TensorFlow `2.x`, installed separately from DeepCTR
- TensorFlow dependency behavior: `deepctr` does not install TensorFlow; choose and install a TensorFlow package that matches Python, NumPy, CPU/GPU, and platform constraints before installing `deepctr`
- Estimator support status: legacy and TensorFlow-version-sensitive. Newer TensorFlow/Keras 3 stacks may import `deepctr` but lack `tf.estimator`.

DeepCTR's own test gate for Estimators accepts TensorFlow versions:

```text
< 2.0.0  OR  >= 2.2.0 and < 2.6.0
```

The repository's current CI also exercises broader TensorFlow 2.x imports with legacy-Keras accommodations, but native Estimator tests remain version-gated. Treat Estimator execution as supported only after the runtime probe succeeds.

## Imports

Preferred public imports for user code:

```python
import tensorflow as tf

from deepctr.estimator import DeepFMEstimator
from deepctr.estimator.inputs import input_fn_tfrecord, input_fn_pandas
```

Use public `tensorflow.keras` APIs in surrounding code. Avoid `tensorflow.python.keras` in user guidance; those modules are private TensorFlow internals.

## Estimator model catalog

All constructors return a `tf.estimator.Estimator` instance. Most constructors accept:

- `linear_feature_columns`: iterable of TensorFlow feature columns for the linear/wide part
- `dnn_feature_columns`: iterable of TensorFlow feature columns for embeddings and dense DNN inputs
- `task`: `"binary"` or `"regression"`
- `model_dir`: directory for checkpoints, graph, summaries, and exported state
- `config`: `tf.estimator.RunConfig`
- `linear_optimizer`: optimizer name or optimizer instance; default commonly `"Ftrl"`
- `dnn_optimizer`: optimizer name or optimizer instance; default commonly `"Adagrad"`
- `training_chief_hooks`: optional iterable of `tf.train.SessionRunHook` objects

| Constructor | Import name | Required feature-column arguments | Main extra knobs |
|---|---|---|---|
| AFM | `AFMEstimator` | `linear_feature_columns`, `dnn_feature_columns` | `use_attention`, `attention_factor`, `l2_reg_att`, `afm_dropout` |
| AutoInt | `AutoIntEstimator` | `linear_feature_columns`, `dnn_feature_columns` | `att_layer_num`, `att_embedding_size`, `att_head_num`, `att_res`, DNN knobs |
| CCPM | `CCPMEstimator` | `linear_feature_columns`, `dnn_feature_columns` | `conv_kernel_width`, `conv_filters`, DNN knobs |
| DCN | `DCNEstimator` | `linear_feature_columns`, `dnn_feature_columns` | `cross_num`, `l2_reg_cross`, DNN knobs |
| DeepFEFM | `DeepFEFMEstimator` | `linear_feature_columns`, `dnn_feature_columns` | field-embedding regularizers, DNN knobs |
| DeepFM | `DeepFMEstimator` | `linear_feature_columns`, `dnn_feature_columns` | DNN hidden units, FM interaction is built in |
| FiBiNET | `FiBiNETEstimator` | `linear_feature_columns`, `dnn_feature_columns` | `bilinear_type`, `reduction_ratio`, DNN knobs |
| FNN | `FNNEstimator` | `linear_feature_columns`, `dnn_feature_columns` | DNN knobs |
| FwFM | `FwFMEstimator` | `linear_feature_columns`, `dnn_feature_columns` | `l2_reg_field_strength`, DNN knobs |
| NFM | `NFMEstimator` | `linear_feature_columns`, `dnn_feature_columns` | `bi_dropout`, DNN knobs |
| PNN | `PNNEstimator` | `dnn_feature_columns` only | `use_inner`, `use_outter`, `kernel_type` in `"mat"`, `"vec"`, `"num"` |
| WDL | `WDLEstimator` | `linear_feature_columns`, `dnn_feature_columns` | Wide+Deep DNN knobs |
| xDeepFM | `xDeepFMEstimator` | `linear_feature_columns`, `dnn_feature_columns` | `cin_layer_size`, `cin_split_half`, `cin_activation`, `l2_reg_cin`, DNN knobs |

The Estimators documented by DeepCTR include CCPM, FNN, PNN, WDL, DeepFM, NFM, AFM, DCN, xDeepFM, AutoInt, and FiBiNET. DeepCTR 0.9.4 source also exposes FwFM and DeepFEFM Estimator constructors from `deepctr.estimator.models`.

## Common constructor pattern

```python
model = DeepFMEstimator(
    linear_feature_columns=linear_feature_columns,
    dnn_feature_columns=dnn_feature_columns,
    dnn_hidden_units=(256, 128, 64),
    dnn_dropout=0.0,
    task="binary",
    model_dir="/tmp/deepctr_deepfm_estimator",  # choose a clean durable path for real jobs
    config=tf.estimator.RunConfig(
        tf_random_seed=2021,
        save_checkpoints_steps=1000,
        keep_checkpoint_max=3,
    ),
    linear_optimizer="Ftrl",
    dnn_optimizer="Adagrad",
)
```

For quick local experiments, `model_dir=None` lets TensorFlow create a temporary model directory, but production or resumable training should pass an explicit path.

## Feature-column identities

Use TensorFlow feature columns, not DeepCTR `SparseFeat`/`DenseFeat`:

```python
cat = tf.feature_column.categorical_column_with_identity(
    key="C1",
    num_buckets=1000,
)
emb = tf.feature_column.embedding_column(cat, dimension=4)
num = tf.feature_column.numeric_column("I1", shape=(1,))

linear_feature_columns = [cat, num]
dnn_feature_columns = [emb, num]
```

Identity columns are appropriate only for integer IDs in range. Hash-bucket categorical columns are safer for raw high-cardinality strings:

```python
cat = tf.feature_column.categorical_column_with_hash_bucket(
    key="ad_id",
    hash_bucket_size=1_000_000,
    dtype=tf.string,
)
```

## Input functions

DeepCTR provides two Estimator input helpers:

```python
input_fn_tfrecord(
    filenames,
    feature_description,
    label=None,
    batch_size=256,
    num_epochs=1,
    num_parallel_calls=8,
    shuffle_factor=10,
    prefetch_factor=1,
)

input_fn_pandas(
    df,
    features,
    label=None,
    batch_size=256,
    num_epochs=1,
    shuffle=False,
    queue_capacity_factor=10,
    num_threads=1,
)
```

`input_fn_tfrecord` returns a zero-argument callable. `input_fn_pandas` delegates to TensorFlow's legacy Pandas input wrapper, using `tf.compat.v1.estimator.inputs.pandas_input_fn` in TensorFlow 2.x when available.

## Estimator outputs and metrics

DeepCTR's Estimator head builds:

- Prediction dictionary: `{"pred": pred, "logits": logits}`
- Export output key: `"predict"`
- Binary loss: sigmoid cross entropy
- Regression loss: mean squared error
- Binary metrics include prediction mean, label mean, log loss, and AUC-like entries
- Regression metrics include MSE and MAE-like entries

Estimator metrics are TensorFlow-version-sensitive in exact key naming. Check for semantic keys rather than relying on one exact full dictionary across releases.

## Optimizer behavior

Constructor optimizer defaults are typically string names:

- `linear_optimizer="Ftrl"` with learning rate `0.005` inside DeepCTR's Estimator utility
- `dnn_optimizer="Adagrad"` with learning rate `0.01` inside DeepCTR's Estimator utility

DeepCTR uses TensorFlow's canned optimizer helper to turn optimizer strings or instances into optimizers. When you need explicit control, pass TensorFlow optimizer instances compatible with the installed Estimator stack.

## `RunConfig`, `model_dir`, and distributed notes

Use `tf.estimator.RunConfig` for Estimator runtime behavior:

```python
config = tf.estimator.RunConfig(
    tf_random_seed=2021,
    save_checkpoints_steps=1000,
    keep_checkpoint_max=3,
    log_step_count_steps=100,
)
```

Guidance:

- `model_dir` owns checkpoints and summaries. Reuse it only when intentionally resuming the same feature schema and constructor shape.
- Change feature names, bucket sizes, embedding dimensions, model family, task type, or hidden-unit shapes -> use a new `model_dir` or remove old checkpoints.
- Estimator distribution is configured through TensorFlow Estimator mechanisms such as `RunConfig`, cluster environment variables, and distribution strategies supported by that TensorFlow version. DeepCTR's constructors do not hide TensorFlow distributed-training requirements.
- For large TFRecord jobs, input sharding, file glob expansion, remote filesystems, worker coordination, and checkpoint retention are TensorFlow Estimator operational concerns; validate a tiny local shard first, then scale.

## Version gate and fallback decision

Use this decision tree:

1. `import tensorflow as tf` succeeds?
2. `hasattr(tf, "estimator")` is true?
3. `tf.estimator.Estimator`, `tf.estimator.RunConfig`, `tf.estimator.ModeKeys`, and `tf.estimator.EstimatorSpec` exist?
4. `deepctr.estimator` and the desired constructor import?
5. Optional: a tiny `DeepFMEstimator` can be constructed with one categorical and one dense feature column?

If any required Estimator gate fails, route the user to Keras-style DeepCTR models. A working `DeepFMEstimator` import alone is not enough: the constructor still needs top-level `tf.estimator` at construction/training time.
