# Troubleshooting

## Import or backend failure

### Symptom
- `ImportError` when importing `vis.visualization` or calling a saliency helper.
- `ValueError` about an unsupported backend.
- TensorFlow graph-mode errors after a modern dependency upgrade.

### Likely cause
- The runtime is not using the legacy standalone Keras + TensorFlow 1.x-compatible stack.
- `protobuf`, TensorFlow, or Keras versions drifted away from the verified legacy combination.

### Recovery
1. Confirm the environment matches the legacy CPU graph-mode stack.
2. Reinstall the pinned compatibility set if dependencies drifted.
3. Avoid mixing in modern Keras/TensorFlow releases for this package.
4. Re-run the smoke script before trying a larger explanation workflow.

## `backprop_modifier` problems

### Symptom
- Guided or rectified saliency produces an error or no visible change.
- A user passes an unsupported modifier name.

### Likely cause
- The modifier name is misspelled or the runtime is using the legacy backend path that does not support the requested modifier.

### Recovery
- Use `guided` for guided backpropagation.
- Use `rectified` or its alias `relu` for clipped-gradient backpropagation.
- Treat `deconv` as an alias for `rectified`.
- On TensorFlow, verify that the model can be saved and reloaded before using the modifier.

## `grad_modifier` problems

### Symptom
- Regression saliency looks inverted, empty, or too noisy.

### Likely cause
- The wrong gradient semantics were chosen for the question being asked.

### Recovery
- Use the default/absolute path to highlight increase in the output.
- Use `negate` to see what decreases the output.
- Use `small_values` to find what preserves the current regression.
- If the map is still hard to read, keep `keepdims=True` and inspect the full gradient tensor shape.

## `keepdims` shape surprises

### Symptom
- Returned heatmap shape does not match expectations.

### Expected behavior
- Image-like inputs with `keepdims=False` collapse the channel axis to a 2D spatial heatmap.
- `keepdims=True` preserves the input-like gradient shape with the batch axis removed.
- Non-image vector inputs may return a 1D gradient when `keepdims=True`.

### Recovery
- Check the model input shape and the input data format.
- For image tensors, verify whether the model expects `channels_first` or `channels_last`.
- For regression vectors, choose `keepdims=True` if you need the full vector gradient.

## Penultimate-layer selection failure

### Symptom
- `ValueError: Unable to determine penultimate Conv or Pooling layer for layer_idx: ...`
- `ValueError: penultimate_layer_idx needs to be before layer_idx`
- Grad-CAM returns a poor or meaningless map.

### Likely cause
- The target layer has no close spatial ancestor.
- The auto-search picked a layer too far from the target.
- The user pointed `penultimate_layer_idx` to the wrong place.

### Recovery
1. Search earlier in the model for the nearest convolutional or pooling layer.
2. Override `penultimate_layer_idx` manually.
3. If the network is dense-only or the spatial layer is too far away, switch to saliency.
4. For wrapper layers, remember that the search skips the wrapper and inspects the wrapped layer.

## Grad-CAM shape or scale problems

### Symptom
- The heatmap size does not match the image or looks uniformly blank.

### Likely cause
- The penultimate feature map is too small, too far away, or the model is not spatial enough for CAM.

### Recovery
- Prefer saliency for dense-only or weakly spatial models.
- Make sure the penultimate layer is the nearest useful convolutional or pooling layer.
- Treat CAM as a spatial localization tool, not a universal explanation method.

## Overlay handoff issues

### Symptom
- A user expects blended visualization output from this sub-skill alone.

### Recovery
- This sub-skill returns the heatmap only.
- Send overlay, colormap, annotation, and image saving requests to `../image-utilities/SKILL.md`.
