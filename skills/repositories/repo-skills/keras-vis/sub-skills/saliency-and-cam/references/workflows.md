# Workflows

## 1. Pick the right explanation style

- Use saliency when you want a general input-gradient explanation.
- Use guided or rectified saliency when you want backprop to suppress negative gradient flow.
- Use Grad-CAM when you want a class-localized spatial explanation from a nearby convolutional or pooling layer.
- Use the `_with_losses` variants when the explanation goal is already expressed as a weighted loss list.

## 2. Saliency for classification or multi-label outputs

1. Choose the target layer, usually the final output layer.
2. Pass one output index or a list of indices.
3. Start with `grad_modifier='absolute'`.
4. Use `keepdims=False` for a compact spatial map; switch to `keepdims=True` if you need the full input-shaped gradient.
5. If the final layer uses softmax and the map is too weak, prefer a linear output for interpretation.

Example pattern:

```python
heatmap = visualize_saliency(model, layer_idx=-1, filter_indices=class_idx, seed_input=x)
```

## 3. Regression attention

For scalar regression outputs, saliency answers three different questions:

- **Increase** the output: default `grad_modifier`.
- **Decrease** the output: `grad_modifier='negate'`.
- **Maintain** the output: `grad_modifier='small_values'`.

Practical sequence:

1. Run the default modifier first.
2. Compare with `negate` to see what drives the output lower.
3. Compare with `small_values` to see what stabilizes the current prediction.
4. If the heatmap is too sparse or noisy, keep `keepdims=True` and inspect the full gradient field.

Example pattern:

```python
increase = visualize_saliency(model, -1, 0, x, grad_modifier='absolute')
decrease = visualize_saliency(model, -1, 0, x, grad_modifier='negate')
maintain = visualize_saliency(model, -1, 0, x, grad_modifier='small_values')
```

## 4. Guided or rectified saliency

Use `backprop_modifier` when you want to change the backward pass itself.

- `guided` keeps only positive gradient flow through positive activations.
- `rectified` and its alias `relu` clip negative gradients.
- The TensorFlow legacy backend is the supported path for this repo release.

Example pattern:

```python
heatmap = visualize_saliency(model, -1, 0, x, backprop_modifier='guided')
```

## 5. Custom-loss saliency

Use `visualize_saliency_with_losses` when the target explanation is already represented as a weighted loss stack.

1. Build the weighted loss list.
2. Choose a `wrt_tensor` only when you want gradients with respect to something other than the model input.
3. Keep the loss definition itself simple; if you need to invent new loss classes or optimizer behavior, hand off to `../optimization-building-blocks/SKILL.md`.
4. Use `keepdims=True` when the output is not image-like.

Example pattern:

```python
losses = [(some_loss, 1.0), (another_loss, -0.2)]
heatmap = visualize_saliency_with_losses(model.input, losses, x, keepdims=True)
```

## 6. Grad-CAM

1. Choose the target layer and class index.
2. Let `penultimate_layer_idx=None` first so the helper can auto-search.
3. If the auto-search chooses a layer that is too far from the target, override it manually.
4. If the model is dense-only or the spatial layer is not close enough, fall back to saliency.
5. If you want a cleaner final picture, route the resulting heatmap to `../image-utilities/SKILL.md` for overlay and image formatting.

Example pattern:

```python
heatmap = visualize_cam(model, layer_idx=-1, filter_indices=class_idx, seed_input=x)
```

## 7. Manual penultimate-layer recovery

Use this sequence when Grad-CAM fails or looks wrong:

1. Inspect the layer order.
2. Find the nearest convolutional or pooling layer that sits before the target.
3. Pass its index as `penultimate_layer_idx`.
4. If you see a `ValueError` about ordering, move the index earlier.
5. If no suitable layer exists, do not force CAM; use saliency instead.

## 8. Overlay handoff

This sub-skill stops at the heatmap.

- Use `../image-utilities/SKILL.md` for overlay, normalization, color conversion, text labels, and stitching.
- Do not duplicate overlay logic here.
