# CAM Generation Troubleshooting

## Blank or all-zero CAM

- The target layer may not influence the target scalar. This is common when
  selecting the final ViT block output after class-token aggregation; route to
  `model-task-adaptation` for transformer layers.
- The target callable may not match the model output shape. For classification,
  start with `ClassifierOutputTarget(class_id)` or `targets=None`.
- The model might be in training mode with stochastic layers. Use `model.eval()`
  for deterministic explanations.
- The selected method may discard negative evidence through ReLU; compare with
  another method from `methods-and-api` if negative evidence matters.

## Shape mismatch

- Expected CAM output shape is `(batch, height, width)` after scaling to the
  input tensor spatial dimensions.
- Input tensors should usually be `B x C x H x W`.
- For non-CNN activations, provide a `reshape_transform` that returns
  `B x C x H x W`; do not force this through core CAM generation alone.

## Visualization errors

- `show_cam_on_image` expects the image as `np.float32` in `[0, 1]`.
- Set `use_rgb=True` when the base image is RGB; OpenCV defaults are BGR.
- Keep `image_weight` between `0` and `1`.

## Slow execution or memory growth

- `ScoreCAM` and `AblationCAM` use repeated forward passes. Set
  `cam.batch_size` and use smaller images for diagnostics.
- Use `with CAMClass(...) as cam:` so hooks are released.
- If repeated calls still grow memory, reduce the loop to a tiny model and run
  the bundled smoke script; then test CUDA-specific memory only in a compatible
  CUDA environment.

## Device mismatch

- Move both `model` and `input_tensor` to the same `torch.device` before
  constructing or calling CAM.
- If a target callable creates tensors, create them on the output tensor's
  device or convert inside `__call__`.
- CPU checks do not verify CUDA/MPS/HPU behavior; run backend smokes first.
