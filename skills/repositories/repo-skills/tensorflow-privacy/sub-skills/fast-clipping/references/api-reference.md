# Fast clipping API reference

## Purpose

Read this for the verified fast-gradient-clipping functions, registry helpers, and sparse-noise support.

## Core functions

### `compute_gradient_norms`

```python
compute_gradient_norms(
    input_model,
    layer_registry,
    x_batch,
    y_batch,
    weight_batch=None,
    per_example_loss_fn=None,
    num_microbatches=None,
    trainable_vars=None,
)
```

Returns a tensor of per-example or per-microbatch gradient norms.

### `compute_clip_weights`

```python
compute_clip_weights(l2_norm_clip, gradient_norms)
```

Returns per-example clip weights from the requested L2 clip and the gradient norms.

### `compute_clipped_gradients_and_outputs`

```python
compute_clipped_gradients_and_outputs(
    input_model,
    registry_fn_outputs_list,
    layer_grad_vars,
    l2_norm_clip,
    x_batch,
    y_batch,
    weight_batch=None,
    num_microbatches=None,
    clipping_loss=None,
)
```

Returns clipped gradients, gradient norms, and clip weights.

## Registry helpers

### `LayerRegistry`

Methods:

- `is_elem(layer_instance)`
- `lookup(layer_instance)`
- `insert(layer_class, layer_registry_function)`

### `make_default_layer_registry`

Returns a registry with at least:

- `tf.keras.layers.Dense`
- `tf.keras.layers.Embedding`

## Sparse-noise support

### `SparsityPreservingNoiseConfig`

Fields:

- `sparse_noise_multiplier=0.0`
- `sparse_selection_threshold=0`
- `sparse_contribution_counts=None`

### `add_aggregate_noise`

```python
add_aggregate_noise(
    clipped_grads,
    batch_size,
    l2_norm_clip,
    noise_multiplier,
    loss_reduction=None,
    loss_model=None,
    sparse_noise_config=None,
)
```

Use this to add dense or sparse noise to already clipped gradients.

## Registry functions

Verified signatures:

- `dense_layer_computation(layer_instance, input_args, input_kwargs, tape, num_microbatches=None)`
- `embedding_layer_computation(layer_instance, input_args, input_kwargs, tape, num_microbatches=None)`
- `layer_normalization_computation(layer_instance, input_args, input_kwargs, tape, num_microbatches=None)`
- `multi_head_attention_layer_computation(layer_instance, input_args, input_kwargs, tape, num_microbatches=None)`
- `einsum_layer_computation(layer_instance, input_args, input_kwargs, tape, num_microbatches=None)`
- `nlp_on_device_embedding_layer_computation(layer_instance, input_args, input_kwargs, tape, num_microbatches=None)`
- `nlp_position_embedding_layer_computation(layer_instance, input_args, input_kwargs, tape, num_microbatches=None)`

## Helper utilities

- `all_trainable_layers_are_registered(input_model, layer_registry) -> bool`
- `generate_model_outputs_using_core_keras_layers(input_model, custom_layer_set=None)`

## Decision points

- Keep the model on the default registry if the core Dense/Embedding path is enough.
- Extend the registry only when the model truly needs a missing layer type.
- Treat the NLP/BERT helpers as optional; they may require extra dependencies beyond the minimum verified environment.
