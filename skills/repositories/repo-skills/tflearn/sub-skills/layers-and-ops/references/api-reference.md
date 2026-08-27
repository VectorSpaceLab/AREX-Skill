# Layers and Ops API Reference

This reference is self-contained for TFLearn graph construction. It summarizes the verified public APIs and the graph side effects that matter when another agent builds or debugs a TFLearn model.

## Compatibility baseline

- Verified package/runtime facts: TFLearn distribution `0.5.0`, TensorFlow `1.15.5`, NumPy `1.18.5`, CPU backend.
- TFLearn imports `tensorflow.compat.v1` internally and disables TensorFlow v2 behavior at import time. In mixed runtimes, explicitly do this before using TFLearn:

  ```python
  import tensorflow.compat.v1 as tf
  tf.disable_v2_behavior()
  import tflearn
  ```

- TFLearn graph objects are TensorFlow v1 graph/session objects. Eager-mode TensorFlow 2 code and modern TensorFlow internals are not a valid assumption for this package.

## Graph initialization and collections

### `tflearn.init_graph`

```python
tflearn.init_graph(seed=None, log_device=False, num_cores=0,
                   gpu_memory_fraction=0, soft_placement=True)
```

Creates a TensorFlow `ConfigProto`, optionally sets the graph random seed, and stores the config in `tf.GraphKeys.GRAPH_CONFIG`. Use it before constructing a `DNN`/session when you need deterministic seeds, CPU thread limits, GPU memory fraction, or device-placement logs. It does not train or initialize variables.

### TFLearn collection keys

Importing TFLearn registers these extra `tf.GraphKeys` names:

| Collection | Populated by | Why it matters |
|---|---|---|
| `tf.GraphKeys.INPUTS` | `input_data`; manually add raw placeholders when bypassing `input_data` | Trainers and feed helpers discover model inputs here. |
| `tf.GraphKeys.TARGETS` | `regression`; `multi_target_data`; manual placeholders passed to `regression` | Trainers and `DNN.fit` discover target placeholders here. |
| `tf.GraphKeys.TRAIN_OPS` | `regression` | Contains `TrainOp` objects, one per optimizer/head. |
| `tf.GraphKeys.LAYER_VARIABLES + "/<scope>"` | layers with variables | Retrieve per-layer weights/biases by layer name or scope. |
| `tf.GraphKeys.LAYER_TENSOR + "/<name>"` | most layers | Retrieve a layer output by name with `tflearn.get_layer_by_name(name)`. |
| `tf.GraphKeys.EXCL_RESTORE_VARS` | layers/variables/regression with `restore=False` | Checkpoint restore should skip these variables/names. |
| `tf.GraphKeys.GRAPH_CONFIG` | `init_graph` | Holds graph/session configuration. |
| `tf.GraphKeys.DATA_PREP` | `input_data(data_preprocessing=...)` | Links preprocessing objects to inputs. Data object construction belongs to `data-input-pipelines`. |
| `tf.GraphKeys.DATA_AUG` | `input_data(data_augmentation=...)` | Links augmentation objects to inputs. |
| `tf.GraphKeys.LR_VARIABLES` | decayed optimizers | Holds decayed learning-rate tensors. |
| `tf.GraphKeys.ACTIVATIONS` | layers/ops that track activations | Used by summaries/visualization helpers. |
| `tf.GraphKeys.REGULARIZATION_LOSSES` | variables/layers with regularizers | Add to total loss when doing manual TensorFlow training. |
| `summary_tags` | summary helpers | Prevents duplicate summary tags and retrieves existing summaries. |
| `is_training`, `is_training_ops` | TFLearn config/training-mode helpers | Controls dropout and batch normalization behavior. |

Validation snippet:

```python
for key in [tf.GraphKeys.INPUTS, tf.GraphKeys.TARGETS, tf.GraphKeys.TRAIN_OPS]:
    print(key, len(tf.get_collection(key)))
```

## Input and core layers

### `input_data`

```python
tflearn.input_data(shape=None, placeholder=None, dtype=tf.float32,
                   data_preprocessing=None, data_augmentation=None,
                   name='InputData')
```

- Provide either `shape` or an existing TensorFlow placeholder.
- Prefer explicit batch dimension: `shape=[None, features]`, `[None, height, width, channels]`, or `[None, timesteps]`.
- If `shape` has more than one dimension and the first item is not `None`, TFLearn prepends `None`. For clarity, pass the batch dimension yourself.
- Adds the placeholder to `INPUTS` and `LAYER_TENSOR/<name>`.
- Stores the supplied preprocessing/augmentation objects in `DATA_PREP` and `DATA_AUG`; it does not create those objects.

### `fully_connected`

```python
tflearn.fully_connected(incoming, n_units, activation='linear', bias=True,
                        weights_init='truncated_normal', bias_init='zeros',
                        regularizer=None, weight_decay=0.001,
                        trainable=True, restore=True, reuse=False,
                        scope=None, name='FullyConnected')
```

- Input: rank >= 2. Non-2D inputs are flattened to `[batch, product_of_non_batch_dims]`.
- Output: rank 2, `[batch, n_units]`.
- String `activation`, `weights_init`, `bias_init`, and `regularizer` values are resolved by TFLearn registries; callables/tensors can be supplied for customization.
- Adds `W` and optionally `b` variables to `LAYER_VARIABLES/<scope_name>` and attaches them to the returned tensor as `.W` and `.b`.
- `scope` overrides `name` for variable scope and reuse. Use `reuse=True` only when the same variables already exist under that scope.
- `restore=False` marks variables for restore exclusion.

### Other core layers

| API | Input/output contract | Notes |
|---|---|---|
| `tflearn.dropout(incoming, keep_prob, noise_shape=None, name='Dropout')` | Same shape as input | `keep_prob` is probability to keep, not drop rate. Uses TFLearn `is_training` variable; at prediction mode it passes input through. |
| `tflearn.reshape(incoming, new_shape, name='Reshape')` | Tensor/list to `new_shape` | Adds output to `LAYER_TENSOR/<name>`. Use `-1` for inferred batch as in TensorFlow. |
| `tflearn.flatten(incoming, name='Flatten')` | Rank >=2 to `[batch, flattened_dims]` | Assertion fails if incoming rank <2. |
| `tflearn.activation(incoming, activation='linear', name='activation')` | Same shape unless activation changes channels | Accepts a string registry name or callable. |
| `tflearn.custom_layer(incoming, custom_fn, **kwargs)` | Whatever `custom_fn` returns | Useful for small TensorFlow ops inside a TFLearn graph; keep custom function deterministic and graph-safe. |
| `tflearn.single_unit(incoming, activation='linear', bias=True, ...)` | Flattens input then outputs one value per sample-like element | Creates scalar/unit weight and bias attributes. Use `fully_connected(..., 1)` for most dense heads. |
| `tflearn.highway(incoming, n_units, activation='linear', transform_dropout=None, ...)` | Rank >=2 to `[batch, n_units]` | Adds transform-gate variables `.W_t`/`.b_t`. Input dimensionality must be compatible with `n_units` for carry path. |
| `tflearn.one_hot_encoding(target, n_classes, on_value=1.0, off_value=0.0)` | Label placeholder to one-hot matrix | Used by `regression(..., to_one_hot=True, n_classes=...)`. |
| `tflearn.time_distributed(incoming, fn, args=None, scope=None)` | Rank >=3 `[batch, timesteps, ...]` to per-timestep transformed tensor | Applies `fn` to every timestep. If `scope` is used, the function must accept a `scope` parameter. |
| `tflearn.multi_target_data(name_list, shape, dtype=tf.float32)` | Creates several target placeholders, concatenates axis 0 | Adds each placeholder to `TARGETS`; use for unusual multi-source target setups. |

## Merge layers and multi-output graph shape

```python
tflearn.merge(tensors_list, mode, axis=1, name='Merge')
tflearn.merge_outputs(tensor_list, name='MergeOutputs')
```

`merge` requires at least two tensors. Modes:

| Mode | Behavior | Shape requirement |
|---|---|---|
| `concat` | `tf.concat(tensors, axis)` | All dimensions except `axis` must match. |
| `elemwise_sum` | Repeated `tf.add` | All tensor shapes must match. |
| `elemwise_mul` | Repeated `tf.multiply` | All tensor shapes must match. |
| `sum`, `mean`, `prod`, `max`, `min` | Concatenate along `axis`, then reduce along `axis` | Tensors must be concat-compatible; output rank is reduced along `axis`. |
| `and`, `or` | Boolean reduction after concat | Use boolean tensors; concat-compatible. |

`merge_outputs` concatenates tensors along axis 1. Use it when separate output tensors should be presented as one prediction tensor. For multiple trainable heads, a common TFLearn pattern is to call `regression` on each head to create one `TrainOp` and target placeholder per head, and then optionally merge the head outputs for prediction.

## Convolution, pooling, and architecture blocks

All convolutional layers support string or callable activations, optional bias, initializers, regularizers, `trainable`, `restore`, `reuse`, `scope`, and `name` when variables are present. Returned tensors from variable-bearing conv layers expose `.W`, `.b`, and `.scope`.

| API family | Expected rank and shape | Key options / notes |
|---|---|---|
| `conv_1d`, `max_pool_1d`, `avg_pool_1d`, `highway_conv_1d` | Rank 3, typically `[batch, width, channels]` | `filter_size`/`kernel_size` and `strides` can be ints or valid lists. |
| `conv_2d`, `atrous_conv_2d`, `grouped_conv_2d`, `max_pool_2d`, `avg_pool_2d`, `highway_conv_2d` | Rank 4, `[batch, height, width, channels]` | `filter_size` int or `[height, width]`; `strides` int, length 2, or full TensorFlow-style length 4; `padding` is `same` or `valid`. `grouped_conv_2d` is depthwise-style and output channels are `input_channels * channel_multiplier`. |
| `conv_2d_transpose` | Rank 4 input; output rank 4 | `output_shape` must be length 2 or 3: `[new_h, new_w]` or `[new_h, new_w, nb_filter]`. |
| `upsample_2d` / `deconv_2d` alias | Rank 4 input; repeats spatial dimensions | `kernel_size` controls spatial upsampling; no learned weights. |
| `upscore_layer` | Rank 4 input | Bilinear-style learned upscore/deconvolution helper for segmentation-like graphs. |
| `conv_3d`, `max_pool_3d`, `avg_pool_3d` | Rank 5, `[batch, depth, height, width, channels]` | 3D filter/kernel/stride helpers accept ints or valid 3D/full TensorFlow forms. |
| `conv_3d_transpose`, `upscore_layer3d` | Rank 5 input; output rank 5 | `output_shape` must be spatial 3D or spatial+channels depending on helper. |
| `global_avg_pool`, `global_max_pool` | Rank >=3 feature maps | Reduces spatial/temporal dimensions to channel summaries. |
| `residual_block`, `residual_bottleneck`, `resnext_block`, `densenet_block` | 2D conv feature maps | Use for compact architecture blocks. For long end-to-end recipes, route to `advanced-model-recipes`. |

Common conv formatter constraints:

- 2D `padding` accepts only `same`, `SAME`, `valid`, or `VALID`.
- 2D `filter_size` accepts an int or a length-2 list/tuple.
- 2D `strides` accepts an int, length-2 list/tuple, or length-4 TensorFlow-style list.
- 3D filters/strides/kernels accept int, length-3, or full length-5 forms where the batch/channel positions are 1.

## Embedding and recurrent layers

### `embedding`

```python
tflearn.embedding(incoming, input_dim, output_dim, validate_indices=False,
                  weights_init='truncated_normal', trainable=True,
                  restore=True, reuse=False, scope=None, name='Embedding')
```

- Input: rank 2 `[batch, ids]`; values are cast to `int32`.
- Output: rank 3 `[batch, ids, output_dim]`.
- Creates `W` of shape `[input_dim, output_dim]`, stored on CPU and attached as `.W`.
- Adds a `.seq_length` tensor computed from nonzero padded ids, used by dynamic recurrent layers.

### Recurrent wrappers

```python
tflearn.simple_rnn(incoming, n_units, activation='sigmoid', dropout=None,
                   return_seq=False, return_state=False, initial_state=None,
                   dynamic=False, ...)
tflearn.lstm(incoming, n_units, activation='tanh', inner_activation='sigmoid',
             dropout=None, forget_bias=1.0, return_seq=False,
             return_state=False, dynamic=False, ...)
tflearn.gru(incoming, n_units, activation='tanh', inner_activation='sigmoid',
            dropout=None, return_seq=False, return_state=False,
            dynamic=False, ...)
tflearn.bidirectional_rnn(incoming, rnncell_fw, rnncell_bw, return_seq=False,
                          return_states=False, dynamic=False, ...)
```

- Input: rank >=3, normally `[batch, timesteps, input_dim]`.
- Default output: rank 2 `[batch, n_units]` containing the last output.
- `return_seq=True`: rank 3 `[batch, timesteps, n_units]`.
- `return_state=True` / `return_states=True`: returns output plus recurrent state(s).
- `dynamic=True`: computes sequence lengths by treating zero-padded timesteps as masked; pad variable-length sequences with zeros at the end.
- `dropout` may be a float keep probability for both input/output or a tuple/list `(input_keep_prob, output_keep_prob)`.
- `bidirectional_rnn` requires forward and backward cells with the same unit count; construct cells with `tflearn.BasicRNNCell`, `tflearn.BasicLSTMCell`, or `tflearn.GRUCell`.
- These wrappers use TensorFlow v1 RNN internals; see troubleshooting before using with modern TensorFlow builds.

## Normalization layers

| API | Contract | Notes |
|---|---|---|
| `tflearn.batch_normalization(incoming, beta=0.0, gamma=1.0, epsilon=1e-5, decay=0.9, ...)` | Same shape as input | Creates beta/gamma plus moving mean/variance. Uses TFLearn `is_training` for batch-vs-moving statistics. Returned tensor exposes `.beta`, `.gamma`, `.scope`. |
| `tflearn.local_response_normalization(incoming, depth_radius=5, bias=1.0, alpha=0.0001, beta=0.75)` | Rank 4 input/output | Thin wrapper around TensorFlow local response normalization. |
| `tflearn.l2_normalize(incoming, dim, epsilon=1e-12)` | Same shape as input | Normalizes along `dim`. |

## Estimator layer: `regression`

```python
tflearn.regression(incoming, placeholder='default', optimizer='adam',
                   loss='categorical_crossentropy', metric='default',
                   learning_rate=0.001, dtype=tf.float32, batch_size=64,
                   shuffle_batches=True, to_one_hot=False, n_classes=None,
                   trainable_vars=None, restore=True, op_name=None,
                   validation_monitors=None, validation_batch_size=None,
                   name=None)
```

`regression` is the bridge from a prediction tensor to TFLearn training metadata. It returns the original `incoming` tensor, not a new prediction transformation.

Side effects:

- If `placeholder='default'`, creates a target placeholder named `Y` under `TargetsData` or `name` scope.
- Adds the target placeholder to `tf.GraphKeys.TARGETS` unless `placeholder=None`.
- If `to_one_hot=True`, requires `n_classes` and one-hot encodes the target placeholder before loss construction.
- Resolves `optimizer`, `loss`, and `metric` strings/classes/callables.
- Creates a `TrainOp` and adds it to `tf.GraphKeys.TRAIN_OPS`.
- Attaches the target placeholder to the returned prediction tensor as `.placeholder` when possible.

Use cases:

```python
net = tflearn.fully_connected(net, 2, activation='softmax')
net = tflearn.regression(net, optimizer='sgd', learning_rate=0.1,
                         loss='categorical_crossentropy', metric='accuracy')
assert len(tf.get_collection(tf.GraphKeys.TRAIN_OPS)) == 1
```

For multiple heads, call `regression` once per head and give distinct `op_name`/`name` values when needed. A shared explicit target placeholder is not duplicated in `TARGETS`.

## Activations

String activations can be passed to layers or `tflearn.activation`. Callables can also be passed.

| Name | Notes |
|---|---|
| `linear` | Identity. |
| `tanh`, `sigmoid`, `softmax`, `softplus`, `softsign` | TensorFlow standard activations. |
| `relu`, `relu6`, `leaky_relu`, `elu`, `crelu`, `selu` | Common neural-network activations. `leaky_relu` has default `alpha=0.1`; pass a callable for custom alpha. |
| `prelu` | Creates trainable alpha variables and supports `channel_shared`, `reuse`, and `scope`. |
| `hard_sigmoid`, `gelu`, `swish`, `mish` | Present in the activation registry. Not all are imported at the package root; use `tflearn.activation(x, 'gelu')` or `tflearn.activations.gelu(x)` if root attribute lookup fails. |

Invalid strings raise an `Invalid activation: <name>`-style error from the registry.

## Objectives / losses

String losses are resolved by `tflearn.objectives.get` and work in `regression(loss='...')`.

| Name | Expected inputs | Notes |
|---|---|---|
| `categorical_crossentropy` | Probabilities and one-hot targets with matching `[batch, classes]` shape | Common with a final `softmax` layer. |
| `softmax_categorical_crossentropy` | Unscaled logits and one-hot targets | Applies softmax internally; do not feed already-softmaxed probabilities. |
| `binary_crossentropy` | Binary logits/targets with same shape | Uses TensorFlow sigmoid-cross-entropy internals; legacy examples often have sigmoid outputs, but logits are the clean design. |
| `weighted_crossentropy` | Binary logits/targets | Supports positive-class weighting. |
| `mean_square` | Predictions/targets same shape | Regression or simple logical examples. |
| `hinge_loss` | Predictions/targets same shape | Margin-style classification. |
| `roc_auc_score` | Binary/probability-like predictions and targets | Approximate AUC objective. |
| `weak_cross_entropy_2d` | `[batch, width, height, classes]` predictions and one-hot targets | Requires `num_classes` or a statically known last dimension. |
| `contrastive_loss` | Pair-distance predictions and binary same/different targets | Metric-learning loss. |
| `triplet_loss` | `anchor`, `positive`, `negative` tensors | Call directly; its signature does not match `regression`'s two-argument loss callable. |

## Metrics

`regression(metric='default')` maps to accuracy except for 1D linear regression, where the default metric is disabled.

| Metric | Construction | Notes |
|---|---|---|
| Accuracy | `tflearn.metrics.Accuracy()` or `metric='accuracy'` | Binary mode for shape `[batch]` or `[batch, 1]` thresholds predictions at `> 0`; categorical mode uses `argmax` on one-hot targets. Tensor has `.m_name` of `binary_acc` or `acc`. |
| Top-k | `tflearn.metrics.Top_k(k=5)` | Use a class instance for custom `k`; string registry also supports default `Top_k`. |
| R2 | `tflearn.metrics.R2()` or exact string `R2` | Coefficient of determination. |
| WeightedR2 | `tflearn.metrics.WeightedR2()` | Requires inputs and targets to have the same shape. |
| Prediction_Counts | `tflearn.metrics.Prediction_Counts(inner_metric)` | Wraps another metric and prints prediction counts. |
| Direct ops | `accuracy_op`, `binary_accuracy_op`, `top_k_op`, `r2_op`, `weighted_r2_op` | Use inside custom TensorFlow graphs. |

Metric classes must be built before `get_tensor()` is used:

```python
metric = tflearn.metrics.Accuracy()
metric.build(predictions, targets, inputs=None)
metric_tensor = metric.get_tensor()
```

## Optimizers

String optimizers are resolved by `tflearn.optimizers.get` inside `regression`. Optimizer classes can also be instantiated and passed in.

| Optimizer | Typical construction | Notes |
|---|---|---|
| SGD | `tflearn.SGD(learning_rate=0.01, lr_decay=0.0, decay_step=100)` | Decay requires a step tensor when built manually. String alias: `sgd`. |
| RMSProp | `tflearn.RMSProp(learning_rate=0.001, decay=0.9, momentum=0.0)` | String alias: `rmsprop`. |
| Adam | `tflearn.Adam(learning_rate=0.001, beta1=0.9, beta2=0.999)` | String alias: `adam`; default for `regression`. |
| Momentum | `tflearn.Momentum(learning_rate=0.001, momentum=0.9, lr_decay=0.0)` | String alias: `momentum`. |
| AdaGrad | `tflearn.AdaGrad(learning_rate=0.001, initial_accumulator_value=0.1)` | String alias: `adagrad`. |
| Ftrl | `tflearn.Ftrl(learning_rate=3.0, learning_rate_power=-0.5, ...)` | String alias: `ftrl`; places optimizer on CPU. |
| AdaDelta | `tflearn.AdaDelta(learning_rate=0.001, rho=0.1, epsilon=1e-08)` | String alias: `adadelta`. |
| ProximalAdaGrad | `tflearn.ProximalAdaGrad(...)` | Alias is `proximaladagrad` (no underscore). |
| Nesterov | `tflearn.Nesterov(learning_rate=0.001, momentum=0.9, ...)` | Uses TensorFlow momentum optimizer with Nesterov enabled. |

Manual optimizer use pattern:

```python
step = tflearn.variable('step', initializer='zeros', shape=[])
optimizer = tflearn.SGD(learning_rate=0.1, lr_decay=0.96, decay_step=200)
optimizer.build(step_tensor=step)
train_optimizer = optimizer.get_tensor()
```

Full training orchestration with `TrainOp`/`Trainer` belongs to `training-and-persistence`; this reference covers only tensors and construction.

## Initializers and regularizers

Initializers accepted by layer arguments such as `weights_init` and `bias_init`:

| Initializer | Notes |
|---|---|
| `zeros` | Constant zero initializer or tensor when `shape` is supplied. |
| `uniform` | Uniform random initializer/tensor. |
| `uniform_scaling` | Unit-scaling style initializer. |
| `normal` | Normal random initializer/tensor. |
| `truncated_normal` | Default dense initializer; truncated normal random values. |
| `xavier` | TensorFlow contrib Xavier initializer; requires TF1 contrib availability. |
| `variance_scaling` | TensorFlow contrib variance-scaling initializer; requires TF1 contrib availability. |

Regularizers:

| Regularizer | Use | Notes |
|---|---|---|
| `L2` | `regularizer='L2', weight_decay=0.001` | Adds half-L2-weighted loss to `REGULARIZATION_LOSSES`. |
| `L1` | `regularizer='L1', weight_decay=0.001` | Adds weighted L1 loss. |

Prefer exact uppercase `L1`/`L2` strings when using layer `regularizer` arguments.

## Variables and layer lookup

```python
tflearn.variable(name, shape=None, dtype=tf.float32, initializer=None,
                 regularizer=None, trainable=True, collections=None,
                 caching_device=None, validate_shape=True, device=None,
                 restore=True)
```

- Wraps `tf.get_variable` and automatically adds variables to global/model collections.
- String initializers and regularizers are resolved through TFLearn registries.
- `device='/cpu:0'` can be used for explicit placement.
- `restore=False` adds the variable to restore-exclusion collections.

Lookup helpers:

| Helper | Result |
|---|---|
| `tflearn.get_all_variables()` | Global variables. |
| `tflearn.get_all_trainable_variable()` | Trainable variables. |
| `tflearn.get_layer_variables_by_name(name)` | Variables in `LAYER_VARIABLES/<name>`. |
| `tflearn.get_layer_variables_by_scope(scope_name)` | Model variables whose names include `scope_name/`. |
| `tflearn.get_layer_by_name(name_or_scope)` | Layer tensor from `LAYER_TENSOR/<name>`, or a list if multiple were registered. |
| `tflearn.variables.get_value(var, session=None)` / `set_value(var, value, session=None)` | Session-backed variable read/write. |
| `tflearn.variables.get_inputs_placeholder_by_name(name)` | Resolves input placeholder from `INPUTS`; accepts TFLearn-style `name/X:0`. |
| `tflearn.variables.get_targets_placeholder_by_name(name)` | Resolves target placeholder from `TARGETS`; accepts TFLearn-style `name/Y:0`. |

Returned layer tensors often expose variables directly:

```python
fc = tflearn.fully_connected(inputs, 64, name='fc1')
print(fc.W, fc.b)
print(tflearn.get_layer_variables_by_name('fc1'))
```

## Summaries and activation monitoring

| API | Purpose |
|---|---|
| `tflearn.summaries.monitor_activation(tensor)` | Adds tensor to `ACTIVATIONS`. |
| `tflearn.summaries.get_summary(stype, tag, value=None, collection_key=None, break_if_exists=False)` | Create/retrieve scalar, histogram, or image summary by tag. |
| `add_activations_summary`, `add_gradients_summary`, `add_trainable_vars_summary` | Add histogram/sparsity summaries to a collection. |
| `add_loss_summaries(total_loss, loss, regul_losses_collection_key, ...)` | Create raw and moving-average loss summaries. |
| `summary_exists(tag)` | Return existing summary tensor if the tag is already registered. |

TFLearn's higher-level summarizer/Trainer verbose behavior is covered by `training-and-persistence`; use this table when wiring summaries manually into a graph.
