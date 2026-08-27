# TFRecord and Pandas Estimator Inputs

DeepCTR's Estimator models do **not** consume Keras-style `SparseFeat` and `DenseFeat` objects. They consume TensorFlow `tf.feature_column` objects and `input_fn` callables that return `(features, labels)` pairs for `tf.estimator.Estimator.train`, `.evaluate`, or `.predict`.

Use this reference when preparing Criteo-style CTR inputs for `DeepFMEstimator` or another DeepCTR Estimator constructor.

## Runtime imports

```python
import tensorflow as tf

from deepctr.estimator import DeepFMEstimator
from deepctr.estimator.inputs import input_fn_tfrecord, input_fn_pandas
```

Run `../scripts/check_estimator_runtime.py` before relying on these imports in a new environment.

## Criteo-style feature names

The common Criteo setup has 26 categorical ID fields, 13 dense numeric fields, and one binary label:

```python
sparse_features = ["C" + str(i) for i in range(1, 27)]
dense_features = ["I" + str(i) for i in range(1, 14)]
label_name = "label"
```

For Estimator workflows, categorical values must already be integer IDs in the valid bucket range. Dense values should be numeric float-like values, usually filled and normalized before input.

## Match `FixedLenFeature` schemas to `tf.feature_column`

A TFRecord schema and feature columns must agree on **feature name**, **dtype**, and **shape**.

### Minimal Criteo schema

```python
feature_description = {
    name: tf.io.FixedLenFeature(shape=(1,), dtype=tf.int64)
    for name in sparse_features
}
feature_description.update({
    name: tf.io.FixedLenFeature(shape=(1,), dtype=tf.float32)
    for name in dense_features
})
feature_description[label_name] = tf.io.FixedLenFeature(shape=(1,), dtype=tf.float32)
```

### Matching feature columns

```python
linear_feature_columns = []
dnn_feature_columns = []

for name in sparse_features:
    cat = tf.feature_column.categorical_column_with_identity(
        key=name,
        num_buckets=1000,  # must be > max serialized id for this field
    )
    linear_feature_columns.append(cat)
    dnn_feature_columns.append(tf.feature_column.embedding_column(cat, dimension=4))

for name in dense_features:
    num = tf.feature_column.numeric_column(key=name, shape=(1,))
    linear_feature_columns.append(num)
    dnn_feature_columns.append(num)
```

Rules:

- `categorical_column_with_identity` expects integer IDs, usually `tf.int64` from `FixedLenFeature`.
- Set `num_buckets` to at least `max_id + 1`. If ID `0` is a padding or unknown bucket, include it in the bucket count.
- Dense scalars should use `tf.float32` TFRecord values and `numeric_column(..., shape=(1,))` or the scalar default shape.
- Dense vectors should use `FixedLenFeature(shape=(dim,), dtype=tf.float32)` plus `numeric_column(name, shape=(dim,))`; do not wrap dense float vectors in `embedding_column`.
- If a sparse feature is already a string in TFRecord, use a string-compatible categorical column such as `categorical_column_with_hash_bucket`, and keep the schema dtype string. Do not use identity columns for strings.

## TFRecord input function recipe

`input_fn_tfrecord(filenames, feature_description, label, ...)` returns a zero-argument `input_fn` suitable for Estimator methods. Internally it creates a `tf.data.TFRecordDataset`, parses each example, pops the label key when provided, batches, repeats, shuffles, and prefetches.

```python
train_input_fn = input_fn_tfrecord(
    filenames=["train.tfrecords"],
    feature_description=feature_description,
    label=label_name,
    batch_size=256,
    num_epochs=1,
    shuffle_factor=10,
    num_parallel_calls=8,
    prefetch_factor=1,
)

eval_input_fn = input_fn_tfrecord(
    filenames=["eval.tfrecords"],
    feature_description=feature_description,
    label=label_name,
    batch_size=16384,
    num_epochs=1,
    shuffle_factor=0,
)
```

Expected records:

- Training/evaluation input returns `(features, labels)` because `label` is not `None`.
- Prediction input should use `label=None`; then the parser leaves all parsed features in the feature dict and returns only `features`.
- Binary tasks expect labels that can be reshaped to `[-1, 1]`; use `float32` labels with values `0.0` or `1.0`.
- Regression tasks use float labels and report regression metrics.

## TFRecord writer schema support

When converting a Pandas row to a serialized `tf.train.Example`, use a writer pattern equivalent to:

```python
def make_example(row, sparse_feature_names, dense_feature_names, label_name):
    features = {
        name: tf.train.Feature(int64_list=tf.train.Int64List(value=[int(row[name])]))
        for name in sparse_feature_names
    }
    features.update({
        name: tf.train.Feature(float_list=tf.train.FloatList(value=[float(row[name])]))
        for name in dense_feature_names
    })
    features[label_name] = tf.train.Feature(
        float_list=tf.train.FloatList(value=[float(row[label_name])])
    )
    return tf.train.Example(features=tf.train.Features(feature=features))
```

This mirrors DeepCTR's maintained TFRecord-generation pattern without requiring a bundled CSV or TFRecord file. For TensorFlow 2.x writers, prefer public APIs:

```python
with tf.io.TFRecordWriter("train.tfrecords") as writer:
    for _, row in train_df.iterrows():
        writer.write(make_example(row, sparse_features, dense_features, label_name).SerializeToString())
```

## Pandas input function recipe

Use `input_fn_pandas(df, features, label, ...)` when the data already fits in memory and a Pandas DataFrame is acceptable.

```python
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, MinMaxScaler

# data = pd.read_csv("your_criteo_like_table.csv")
data[sparse_features] = data[sparse_features].fillna("-1")
data[dense_features] = data[dense_features].fillna(0.0)

for name in sparse_features:
    encoder = LabelEncoder()
    data[name] = encoder.fit_transform(data[name]).astype("int64")

scaler = MinMaxScaler(feature_range=(0, 1))
data[dense_features] = scaler.fit_transform(data[dense_features]).astype("float32")
data[label_name] = data[label_name].astype("float32")

train_df, test_df = train_test_split(data, test_size=0.2, random_state=2021)

train_input_fn = input_fn_pandas(
    train_df,
    features=sparse_features + dense_features,
    label=label_name,
    batch_size=256,
    num_epochs=1,
    shuffle=True,
)
predict_input_fn = input_fn_pandas(
    test_df,
    features=sparse_features + dense_features,
    label=None,
    batch_size=4096,
    num_epochs=1,
    shuffle=False,
)
```

Dense default handling is your preprocessing responsibility. Fill missing dense columns before calling `input_fn_pandas`; otherwise TensorFlow's Pandas input wrapper may infer unexpected dtypes or feed `NaN` values into numeric columns.

## Train, evaluate, predict

```python
model = DeepFMEstimator(
    linear_feature_columns,
    dnn_feature_columns,
    task="binary",
    config=tf.estimator.RunConfig(tf_random_seed=2021),
)

model.train(train_input_fn)
eval_result = model.evaluate(eval_input_fn)
predictions = list(model.predict(predict_input_fn))
```

Expected output shapes and keys:

- `evaluate` returns a metrics dictionary. Binary tasks include loss-like values and AUC-related metric keys; exact key names can vary by TensorFlow version.
- `predict` yields dictionaries with at least `"pred"` and `"logits"` keys from DeepCTR's Estimator head. `pred` has shape `(1,)` per example for binary/regression scores.
- If `label=None` during prediction, do not compute sklearn metrics against the input function output; compute metrics from the original held-out DataFrame labels.

## Feature-column variations

### Hash buckets for high-cardinality strings

```python
cat = tf.feature_column.categorical_column_with_hash_bucket(
    key="ad_id",
    hash_bucket_size=1_000_000,
    dtype=tf.string,
)
dnn_feature_columns.append(tf.feature_column.embedding_column(cat, dimension=8))
linear_feature_columns.append(cat)
```

### Dense vector feature

```python
feature_description["user_vector"] = tf.io.FixedLenFeature(shape=(64,), dtype=tf.float32)
vec = tf.feature_column.numeric_column("user_vector", shape=(64,))
dnn_feature_columns.append(vec)
linear_feature_columns.append(vec)
```

### Padded integer sequence as a fixed vector

DeepCTR Estimator APIs use TensorFlow feature columns, not `VarLenSparseFeat`. If a fixed-length padded sequence is used, store it as an integer vector and choose TensorFlow feature-column handling deliberately. For many DeepCTR Estimator architectures, simple scalar categorical and dense features are the most reliable path; sequence-model semantics are better covered by Keras-style sequence workflows.

## Validation checklist

Before launching a large job:

1. Run `../scripts/check_estimator_runtime.py --construct-estimator`.
2. Confirm every model feature appears in the input function's feature dict and every label key is absent from the feature dict when `label` is set.
3. Assert sparse ID min/max values are inside `[0, num_buckets)`.
4. Assert dense columns are finite `float32` arrays with expected shapes.
5. Parse a small TFRecord batch with the same `feature_description` before training.
6. Use a new or empty `model_dir` after changing feature schema or constructor hyperparameters that affect variable shapes.
