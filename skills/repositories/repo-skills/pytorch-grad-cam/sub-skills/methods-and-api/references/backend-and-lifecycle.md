# Backend and Lifecycle Notes

## BaseCAM lifecycle

`BaseCAM` wraps the model with hook registration via an
`ActivationsAndGradients` helper. The important lifecycle rule is to release
hooks when finished.

Preferred usage:

```python
with GradCAM(model=model, target_layers=[model.layer4[-1]]) as cam:
    grayscale_cam = cam(input_tensor=input_tensor, targets=targets)
```

`__exit__` releases hooks and swallows an `IndexError` raised inside the `with`
block after printing a short message. If you construct the CAM object manually,
call `release()` or let the context manager do it for you.

## Device selection

- The CAM object uses the device of `next(model.parameters()).device`.
- Move the model and input tensor to the same device before calling CAM.
- CUDA checks are useful only after `torch.cuda.is_available()` reports true.
- On HPU, `BaseCAM` imports `habana_frameworks.torch.core` and stores it as
  `_htcore`; future agents should preserve that underscore-prefixed attribute.

## Batch and target behavior

- If `targets is None`, `BaseCAM` creates `ClassifierOutputTarget` objects from
  the argmax class for each batch member.
- `targets` should normally contain one callable per batch member.
- `ScoreCAM` and `AblationCAM` use batched forward passes and may need a custom
  `batch_size` for performance.

## Expert method behaviors

- `FinerCAM` uses a base CAM and default comparison categories `[1, 2, 3]`
  clamped by the number of available classes.
- `SegEigenCAM` multiplies absolute gradients by activations before eigen
  projection and then applies sign correction.
- `KPCA_CAM` exposes kernel/gamma options that can change the projection.
- `GuidedBackpropReLUModel` needs the same device string as the model.
