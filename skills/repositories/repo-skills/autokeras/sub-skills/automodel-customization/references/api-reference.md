# AutoModel Customization API Reference

## `ak.AutoModel`

```python
ak.AutoModel(inputs, outputs, project_name="auto_model", max_trials=100,
             directory=None, objective="val_loss", tuner="greedy",
             overwrite=False, seed=None, max_model_size=None, **kwargs)
```

Use input/output API by supplying input nodes and output heads, or functional API by manually calling blocks on nodes and passing final output nodes.

## Input nodes

```python
ak.Input(name=None, **kwargs)
ak.ImageInput(name=None, **kwargs)
ak.TextInput(name=None, **kwargs)
ak.StructuredDataInput(column_names=None, column_types=None, name=None, **kwargs)
```

## Wrapper blocks

```python
ak.ImageBlock(block_type=None, normalize=None, augment=None, **kwargs)
ak.TextBlock(max_tokens=None, **kwargs)
ak.StructuredDataBlock(normalize=None, **kwargs)
```

`ImageBlock` can tune among `"resnet"`, `"xception"`, `"vanilla"`, and `"efficient"` when `block_type=None`.

## Basic blocks and reductions

```python
ak.DenseBlock(num_layers=None, num_units=None, use_batchnorm=None, dropout=None, **kwargs)
ak.ConvBlock(kernel_size=None, num_blocks=None, num_layers=None, filters=None, max_pooling=None, separable=None, dropout=None, **kwargs)
ak.RNNBlock(return_sequences=False, bidirectional=None, num_layers=None, layer_type=None, **kwargs)
ak.ResNetBlock(version=None, pretrained=None, **kwargs)
ak.XceptionBlock(pretrained=None, **kwargs)
ak.EfficientNetBlock(version=None, pretrained=None, **kwargs)
ak.Embedding(max_features=20001, embedding_dim=None, dropout=None, **kwargs)
ak.Merge(merge_type=None, **kwargs)
ak.SpatialReduction(reduction_type=None, **kwargs)
ak.TemporalReduction(reduction_type=None, **kwargs)
ak.Flatten(**kwargs)
ak.Normalization(axis=-1, **kwargs)
ak.ImageAugmentation(translation_factor=None, vertical_flip=None, horizontal_flip=None, rotation_factor=None, zoom_factor=None, contrast_factor=None, **kwargs)
```

Parameters left as `None` usually become tunable hyperparameters. Supply concrete values when a fixed search space is required.

## Heads

```python
ak.ClassificationHead(num_classes=None, multi_label=False, loss=None, metrics=None, dropout=None, **kwargs)
ak.RegressionHead(output_dim=None, loss="mean_squared_error", metrics=None, dropout=None, **kwargs)
```

A graph output branch should end with a head unless you intentionally pass already-headed output nodes.

## Composition rules

- Every output must be reachable from the declared inputs.
- Every block input must be present in the reachable graph.
- The graph must not contain cycles.
- At `fit`/`predict` time, the nested structure of `x` must match `inputs`; the nested structure of `y` must match output heads.
- Use `ak.Merge()` when multiple branches must combine before a shared head.
