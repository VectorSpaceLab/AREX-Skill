# Fast clipping troubleshooting

## Unsupported layer in the registry

### Symptom
- The registry check fails or a model path falls back to the slow implementation.

### Likely cause
- The model uses a layer type that is not present in the default registry.

### Recovery
- Call `all_trainable_layers_are_registered()` first.
- If the model uses a missing layer, either extend the registry or keep using the plain DP optimizer path.

## Loss reduction mismatch

### Symptom
- `compute_gradient_norms()` or `add_aggregate_noise()` behaves unexpectedly.

### Likely cause
- The loss reduction is incompatible with the fast clipping path.
- Microbatching is enabled but the loss is not being treated as a mean over the microbatch.

### Recovery
- Check the model loss reduction before trying to debug the clipping math.
- Use the tiny fast-clipping smoke helper to confirm the basic path.

## Sparse gradient noise confusion

### Symptom
- Sparse gradients do not receive the expected noise treatment.

### Likely cause
- `sparse_noise_config` was not supplied.
- The gradient is not an `IndexedSlices` object, so the dense noise path is used.

### Recovery
- Treat sparse noise as optional configuration.
- Confirm that the model actually produces sparse gradients before changing the noise settings.

## Optional NLP/BERT helpers fail to import

### Symptom
- `bert_encoder_utils` or an NLP registry function fails because of missing optional dependencies.

### Likely cause
- The extra `tensorflow_models` / `tensorflow_hub` / TFDS stack is absent.

### Recovery
- Keep the minimum verified scope on the core Dense / Embedding / LayerNormalization / attention helpers.
- Prepare the optional dependency stack separately before claiming that path.

## Registry coverage confusion

### Symptom
- A user expects `make_default_layer_registry()` to support every layer.

### Likely cause
- The default registry only covers the core layers needed by the common fast-clipping path.

### Recovery
- Explain the default coverage explicitly.
- Extend only the layers needed by the user's model.
