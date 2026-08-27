# API Reference

This page records the DeepCTR 0.9.4 Keras API surface used by this sub-skill.

## Package facts

- Distribution/import name: `deepctr`
- Version: `0.9.4`
- Python: `>=3.7`
- TensorFlow: compatible with TensorFlow 1.15 and 2.x; TensorFlow is installed separately.
- Recommended user imports: public `tensorflow.keras`, not private `tensorflow.python.keras`.

## Constructor families

All constructors below return a `tensorflow.keras.models.Model` instance unless noted.

Most fixed-length models accept the same two-column split:

```python
model = ModelName(linear_feature_columns, dnn_feature_columns, task="binary")
```

`linear_feature_columns` feed the linear/wide part. `dnn_feature_columns` feed embeddings, dense inputs, cross layers, DNNs, or interaction layers. For basic use, pass the same feature-column list to both.

## Verified Keras model constructors

```python
from deepctr.models import (
    AFM, AutoInt, CCPM, DCN, DCNMix, DeepFEFM, DeepFM, DIFM, EDCN,
    FGCNN, FiBiNET, FLEN, FNN, FwFM, IFM, MLR, NFM, ONN, PNN, WDL, xDeepFM,
)
```

### General baselines

```python
DeepFM(linear_feature_columns, dnn_feature_columns,
       fm_group=("default_group",), dnn_hidden_units=(256, 128, 64),
       l2_reg_linear=1e-5, l2_reg_embedding=1e-5, l2_reg_dnn=0,
       seed=1024, dnn_dropout=0, dnn_activation="relu", dnn_use_bn=False,
       task="binary")

WDL(linear_feature_columns, dnn_feature_columns,
    dnn_hidden_units=(256, 128, 64), l2_reg_linear=1e-5,
    l2_reg_embedding=1e-5, l2_reg_dnn=0, seed=1024,
    dnn_dropout=0, dnn_activation="relu", task="binary")

FNN(linear_feature_columns, dnn_feature_columns,
    dnn_hidden_units=(256, 128, 64), l2_reg_embedding=1e-5,
    l2_reg_linear=1e-5, l2_reg_dnn=0, seed=1024,
    dnn_dropout=0, dnn_activation="relu", task="binary")
```

### Pairwise/product/FM models

```python
AFM(linear_feature_columns, dnn_feature_columns, fm_group="default_group",
    use_attention=True, attention_factor=8, l2_reg_linear=1e-5,
    l2_reg_embedding=1e-5, l2_reg_att=1e-5, afm_dropout=0,
    seed=1024, task="binary")

NFM(linear_feature_columns, dnn_feature_columns,
    dnn_hidden_units=(256, 128, 64), l2_reg_embedding=1e-5,
    l2_reg_linear=1e-5, l2_reg_dnn=0, seed=1024,
    bi_dropout=0, dnn_dropout=0, dnn_activation="relu", task="binary")

PNN(dnn_feature_columns, dnn_hidden_units=(256, 128, 64),
    l2_reg_embedding=1e-5, l2_reg_dnn=0, seed=1024,
    dnn_dropout=0, dnn_activation="relu", use_inner=True,
    use_outter=False, kernel_type="mat", task="binary")

IFM(linear_feature_columns, dnn_feature_columns,
    dnn_hidden_units=(256, 128, 64), l2_reg_linear=1e-5,
    l2_reg_embedding=1e-5, l2_reg_dnn=0, seed=1024,
    dnn_dropout=0, dnn_activation="relu", dnn_use_bn=False,
    task="binary")

DIFM(linear_feature_columns, dnn_feature_columns,
     att_embedding_size=8, att_head_num=8, att_res=True,
     dnn_hidden_units=(256, 128, 64), l2_reg_linear=1e-5,
     l2_reg_embedding=1e-5, l2_reg_dnn=0, seed=1024,
     dnn_dropout=0, dnn_activation="relu", dnn_use_bn=False,
     task="binary")
```

### Cross/attention/high-order interaction models

```python
DCN(linear_feature_columns, dnn_feature_columns, cross_num=2,
    cross_parameterization="vector", dnn_hidden_units=(256, 128, 64),
    l2_reg_linear=1e-5, l2_reg_embedding=1e-5, l2_reg_cross=1e-5,
    l2_reg_dnn=0, seed=1024, dnn_dropout=0, dnn_use_bn=False,
    dnn_activation="relu", task="binary")

DCNMix(linear_feature_columns, dnn_feature_columns, cross_num=2,
       dnn_hidden_units=(256, 128, 64), l2_reg_linear=1e-5,
       l2_reg_embedding=1e-5, low_rank=32, num_experts=4,
       l2_reg_cross=1e-5, l2_reg_dnn=0, seed=1024,
       dnn_dropout=0, dnn_use_bn=False, dnn_activation="relu",
       task="binary")

xDeepFM(linear_feature_columns, dnn_feature_columns,
        dnn_hidden_units=(256, 128, 64), cin_layer_size=(128, 128),
        cin_split_half=True, cin_activation="relu", l2_reg_linear=1e-5,
        l2_reg_embedding=1e-5, l2_reg_dnn=0, l2_reg_cin=0,
        seed=1024, dnn_dropout=0, dnn_activation="relu",
        dnn_use_bn=False, task="binary")

AutoInt(linear_feature_columns, dnn_feature_columns, att_layer_num=3,
        att_embedding_size=8, att_head_num=2, att_res=True,
        dnn_hidden_units=(256, 128, 64), dnn_activation="relu",
        l2_reg_linear=1e-5, l2_reg_embedding=1e-5, l2_reg_dnn=0,
        dnn_use_bn=False, dnn_dropout=0, seed=1024, task="binary")

EDCN(linear_feature_columns, dnn_feature_columns, cross_num=2,
     cross_parameterization="vector", bridge_type="concatenation", tau=1.0,
     l2_reg_linear=1e-5, l2_reg_embedding=1e-5, l2_reg_cross=1e-5,
     l2_reg_dnn=0, seed=1024, dnn_dropout=0, dnn_use_bn=False,
     dnn_activation="relu", task="binary")
```

### Field-aware and convolutional models

```python
FiBiNET(linear_feature_columns, dnn_feature_columns,
        bilinear_type="interaction", reduction_ratio=3,
        dnn_hidden_units=(256, 128, 64), l2_reg_linear=1e-5,
        l2_reg_embedding=1e-5, l2_reg_dnn=0, seed=1024,
        dnn_dropout=0, dnn_activation="relu", task="binary")

FLEN(linear_feature_columns, dnn_feature_columns,
     dnn_hidden_units=(256, 128, 64), l2_reg_linear=1e-5,
     l2_reg_embedding=1e-5, l2_reg_dnn=0, seed=1024,
     dnn_dropout=0.0, dnn_activation="relu", dnn_use_bn=False,
     task="binary")

FwFM(linear_feature_columns, dnn_feature_columns, fm_group=("default_group",),
     dnn_hidden_units=(256, 128, 64), l2_reg_linear=1e-5,
     l2_reg_embedding=1e-5, l2_reg_field_strength=1e-5,
     l2_reg_dnn=0, seed=1024, dnn_dropout=0,
     dnn_activation="relu", dnn_use_bn=False, task="binary")

FGCNN(linear_feature_columns, dnn_feature_columns,
      conv_kernel_width=(7, 7, 7, 7), conv_filters=(14, 16, 18, 20),
      new_maps=(3, 3, 3, 3), pooling_width=(2, 2, 2, 2),
      dnn_hidden_units=(256, 128, 64), l2_reg_linear=1e-5,
      l2_reg_embedding=1e-5, l2_reg_dnn=0, dnn_dropout=0,
      seed=1024, task="binary")

CCPM(linear_feature_columns, dnn_feature_columns,
     conv_kernel_width=(6, 5), conv_filters=(4, 4),
     dnn_hidden_units=(128, 64), l2_reg_linear=1e-5,
     l2_reg_embedding=1e-5, l2_reg_dnn=0, dnn_dropout=0,
     seed=1024, task="binary")

ONN(linear_feature_columns, dnn_feature_columns,
    dnn_hidden_units=(256, 128, 64), l2_reg_embedding=1e-5,
    l2_reg_linear=1e-5, l2_reg_dnn=0, dnn_dropout=0,
    seed=1024, use_bn=True, reduce_sum=False, task="binary")

DeepFEFM(linear_feature_columns, dnn_feature_columns, use_fefm=True,
         dnn_hidden_units=(256, 128, 64), l2_reg_linear=1e-5,
         l2_reg_embedding_feat=1e-5, l2_reg_embedding_field=1e-5,
         l2_reg_dnn=0, seed=1024, dnn_dropout=0.0,
         exclude_feature_embed_in_dnn=False, use_linear=True,
         use_fefm_embed_in_dnn=True, dnn_activation="relu",
         dnn_use_bn=False, task="binary")
```

### Piecewise linear model

```python
MLR(region_feature_columns, base_feature_columns=None, region_num=4,
    l2_reg_linear=1e-5, seed=1024, task="binary",
    bias_feature_columns=None)
```

`MLR` is less interchangeable with the other two-list model constructors. Use `region_feature_columns` for region assignment, optionally a separate `base_feature_columns`, and optional `bias_feature_columns`.

## Important constraints

- `task` is normally `"binary"` or `"regression"` for this sub-skill. DeepCTR's `PredictionLayer` also recognizes `"multiclass"`, but the fixed-length CTR model examples here focus on binary/regression.
- `DCN` and `DCNMix` require either `dnn_hidden_units` or `cross_num` to be non-empty/non-zero.
- `AutoInt` requires either `dnn_hidden_units` or `att_layer_num` to be non-empty/non-zero.
- `EDCN` requires `cross_num > 0`.
- `PNN` uses only `dnn_feature_columns`; do not pass a linear column list as the first argument.
- `PNN(kernel_type=...)` accepts `"mat"`, `"vec"`, or `"num"`.
- `FGCNN` requires `conv_kernel_width`, `conv_filters`, `new_maps`, and `pooling_width` to have the same length.
- `AFM`, `CCPM`, and `EDCN` call the feature-column extraction path with dense support disabled for their main interaction branch; do not use them as first choices for dense-only tasks.
- `IFM` and `DIFM` require non-empty `dnn_hidden_units` and sparse features.
- `SparseFeat(dtype="string")` requires `use_hash=True`; otherwise encode string categories to integer ids first.

## Input contract

Feature columns are defined by `deepctr.feature_column`:

```python
from deepctr.feature_column import SparseFeat, DenseFeat, VarLenSparseFeat, get_feature_names

SparseFeat(name, vocabulary_size, embedding_dim=4, use_hash=False,
           vocabulary_path=None, dtype="int32", embeddings_initializer=None,
           embedding_name=None, group_name="default_group", trainable=True)

DenseFeat(name, dimension=1, dtype="float32", transform_fn=None)

VarLenSparseFeat(sparsefeat, maxlen, combiner="mean",
                 length_name=None, weight_name=None, weight_norm=True)
```

For Keras models, `model_input` should be a dictionary whose keys are exactly `get_feature_names(linear_feature_columns + dnn_feature_columns)` and whose values are NumPy arrays, Pandas Series, or tensors with the same first dimension.

## Keras method contracts

### `compile`

```python
model.compile(optimizer, loss=None, metrics=None, loss_weights=None,
              sample_weight_mode=None, weighted_metrics=None,
              target_tensors=None)
```

Use `optimizer` as a string or `tf.keras.optimizers.Optimizer`. Match loss to `task`:

- binary: `"binary_crossentropy"`
- regression: `"mse"` or another regression loss

### `fit`

```python
history = model.fit(x=None, y=None, batch_size=None, epochs=1, verbose=1,
                    callbacks=None, validation_split=0.0,
                    validation_data=None, shuffle=True, class_weight=None,
                    sample_weight=None, initial_epoch=0,
                    steps_per_epoch=None, validation_steps=None,
                    validation_freq=1)
```

For DeepCTR dict inputs, `x` is usually `model_input`, and `y` is a shape `(n, 1)` or `(n,)` target array. Returns a `History` object whose `.history` maps metric names to per-epoch values.

### `evaluate`

```python
result = model.evaluate(x=None, y=None, batch_size=None, verbose=1,
                        sample_weight=None, steps=None, callbacks=None)
```

Returns a scalar loss or a list of scalars. Use `model.metrics_names` to label list outputs.

### `predict`

```python
pred = model.predict(x, batch_size=None, verbose=0, steps=None, callbacks=None)
```

For single-output DeepCTR models in this sub-skill, `pred` should have shape `(n, 1)`.

### Batch and generator methods

The same Keras contracts apply for `train_on_batch`, `test_on_batch`, `predict_on_batch`, `fit_generator`, `evaluate_generator`, and `predict_generator`. Prefer `fit` with dict inputs or `tf.data` unless the user already has a generator.

## Persistence API

```python
from tensorflow.keras.models import save_model, load_model
from deepctr.layers import custom_objects

save_model(model, "model.h5")
loaded = load_model("model.h5", custom_objects=custom_objects)
```

`deepctr.layers.custom_objects` includes DeepCTR layers needed by serialized models, such as `DNN`, `PredictionLayer`, `FM`, `AFMLayer`, `CrossNet`, `CrossNetMix`, `CIN`, `InteractingLayer`, `FGCNNLayer`, `SENETLayer`, `BilinearInteraction`, `FieldWiseBiInteraction`, `FwFMLayer`, `FEFMLayer`, `RegulationModule`, `BridgeModule`, and related utilities.

For long-lived projects, prefer weights-only saves plus reconstructing the model from feature columns and constructor arguments.
