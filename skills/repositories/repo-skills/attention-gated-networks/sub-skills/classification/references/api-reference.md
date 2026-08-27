# Classification API Reference

## Purpose

Read this when a task needs exact class names, configuration fields, or runtime
objects for the ultrasound classification path. These notes are distilled from
the package source and live package inspection.

## Entry points

| Object | Signature or command | Use |
| --- | --- | --- |
| `models.get_model(json_opts)` | `(json_opts)` | Builds a wrapper model from a JSON-style object. For classification, `json_opts.type` is `classifier` or `aggregated_classifier`. |
| `dataio.loader.get_dataset(name)` | `(name)` | Returns dataset class. Use `name='us'` for ultrasound HDF5 classification. |
| `dataio.loader.get_dataset_path(dataset_name, opts)` | `(dataset_name, opts)` | Looks up the dataset path as `getattr(opts, dataset_name)`. |
| `dataio.transformation.get_dataset_transformation(name, opts=None)` | `(name, opts=None)` | Builds transform dictionaries. `name='us'` returns `train` and `valid` transforms. |
| `scripts/run_classifier.py` | `--config CONFIG --mode train|test [--repo-root PATH] [--disable-visdom]` | Skill-owned replacement; relative configs require `--repo-root` and config-relative data paths use the config parent. |
| Source root entry points | `train_classifaction.py -c CONFIG`; `test_classification.py -c CONFIG` | Evidence for script behavior; use the bundled replacement unless you are deliberately working inside a maintainer checkout. |

## Model selection

`models.__init__.ModelOpts` translates the `model` block of a config into the
fields used by the wrapper classes. The important classification fields are:

| Config field | Values seen in configs | Notes |
| --- | --- | --- |
| `type` | `classifier`, `aggregated_classifier` | Selects `FeedForwardClassifier` or `AggregatedClassifier`. |
| `model_type` | `sononet2`, `sononet_grid_attention` | Passed to `models.networks.get_network`. `sononet` is also implemented. |
| `tensor_dim` | `2D` | Classification models are 2D. |
| `input_nc` | `1` | Ultrasound configs use a single grayscale channel. |
| `output_nc` | `14` | The ultrasound HDF5 file must contain 14 label names for the bundled configs. |
| `feature_scale` | `8` | Divides channel counts in Sononet blocks. |
| `gpu_ids` | `[0]` | Non-empty lists trigger CUDA model and tensor moves. |
| `criterion` | `cross_entropy` | Uses `torch.nn.CrossEntropyLoss` for classifier wrappers. |
| `nonlocal_mode` | `concatenation_mean_flow` | Used by grid-attention classifiers. |
| `aggregation_mode` | `mean`, `deep_sup`, `ft`, `concat` | Controls classifier heads and output structure in `sononet_grid_attention`. |
| `weight`, `aggregation`, `aggregation_param` | config-dependent | Used by `AggregatedClassifier` to weight/decode deep supervision predictions. |

## Core classes

### `FeedForwardClassifier`

The wrapper is defined in `models/feedforward_classifier.py`.

- `initialize(self, opts, **kwargs)` creates the network, moves it to CUDA when
  `self.use_cuda` is true, loads a checkpoint when `not opts.isTrain` or
  `opts.continue_train`, and creates the criterion/optimizer when training.
- `set_input(self, *inputs)` expects image tensors first and label tensors
  second. If a 5D tensor is supplied with `tensor_dim='2D'`, it reshapes from
  `(B, C, H, W, Z)` to `(B*Z, C, H, W)`.
- `forward(self, split)` uses `Variable(self.input)` for training and inference,
  then applies the network's `apply_argmax_softmax` method on validation/test.
- `validate(self)` runs a forward pass, computes cross entropy, and accumulates
  labels/probabilities.
- `get_classification_stats(self)` reports accuracy, confusion matrix, macro F1,
  precision, recall, and a per-class breakdown.

### `AggregatedClassifier`

`AggregatedClassifier` subclasses `FeedForwardClassifier` and handles networks
that return multiple predictions, such as deep-supervision attention models.
The aggregation modes in the source are:

| `aggregation` | Behavior |
| --- | --- |
| `max` | Uses the maximum softmax score across predictions and classes. |
| `mean` | Averages softmax scores across predictions, then selects the max class. |
| `weighted_mean` | Multiplies prediction scores by `weight` before averaging. |
| `idx` | Selects `aggregation_param` from the prediction list. |

The implementation creates aggregation weights with `.cuda()`, so this path is
not a CPU-only path without source edits.

### Sononet models

| Class/function | Signature | Notes |
| --- | --- | --- |
| `models.networks.sononet.sononet` | `(feature_scale=4, n_classes=21, in_channels=3, is_batchnorm=True, n_convs=None)` | VGG-like 2D classifier that pools class logits with adaptive average pooling. |
| `models.networks.sononet.sononet2` | `(feature_scale=4, n_classes=21, in_channels=3, is_batchnorm=True)` | Uses convolution counts `[3,3,3,2,2]`. |
| `models.networks.sononet_grid_attention.sononet_grid_attention` | `(feature_scale=4, n_classes=21, in_channels=3, is_batchnorm=True, n_convs=None, nonlocal_mode='concatenation', aggregation_mode='concat')` | Adds attention blocks over `conv3` and `conv4`, with `conv5` as the gating signal. |
| `GridAttentionBlock2D_TORR` | `(in_channels, gating_channels, inter_channels=None, mode='concatenation', sub_sample_factor=(1, 1), bn_layer=True, use_W=True, use_phi=True, use_theta=True, use_psi=True, nonlinearity1='relu')` | Attention block used by the 2D grid-attention classifier. |

## Data and transform APIs

`UltraSoundDataset(root_path, split, transform=None, preload_data=False)` reads a
single HDF5 file. For a split such as `train`, `val`, or `test`, it expects:

- images in `x_<split>`;
- labels in `p_<split>`;
- UTF-8 label bytes in `label_names`;
- class labels as integers compatible with `output_nc`.

The dataset computes per-sample weights from inverse class frequencies. The
training script then uses either a custom `StratifiedSampler`,
`WeightedRandomSampler`, or a background-upweighted sampler depending on
`training.sampler`.

The ultrasound transform builder returns:

- `train`: tensor conversion, float type cast, add channel, special crop,
  random horizontal flip, random affine, and standard normalization;
- `valid`: tensor conversion, add channel, special crop, and standard
  normalization.

## Metrics and logging

`models.utils.classification_stats(pred_seg, target, labels)` delegates to
scikit-learn accuracy, F1, precision, recall, and confusion-matrix functions.
`utils.error_logger.ErrorLogger` tracks scalar and table-like values per split.
Legacy code uses `np.float` in `StatLogger`; avoid this class in new bundled
helpers unless the runtime NumPy version still provides that alias.
