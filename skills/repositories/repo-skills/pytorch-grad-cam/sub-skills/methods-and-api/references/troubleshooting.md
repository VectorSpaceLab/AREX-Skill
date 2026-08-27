# Methods and API Troubleshooting

## `FinerCAM` on small-class classifiers

The default comparison slice is clamped to the number of available classes.
Binary and ternary classifiers should not raise `IndexError`; if they do, the
skill should mention the existing regression test and the comparison-category
clamping logic.

## Unexpectedly flat or noisy results

- Compare several methods: GradCAM, HiResCAM, GradCAMPlusPlus, and LayerCAM.
- Try a deeper or earlier target layer.
- For transformers, route to `model-task-adaptation` and confirm the reshape
  transform before judging the method.
- For `ScoreCAM` or `AblationCAM`, check that the batch size is large enough to
  be practical but not so large that memory blows up.

## Hook leaks or context-manager bugs

- Always prefer `with CAMClass(...) as cam:`.
- If a loop creates many CAM objects, ensure each object is released at exit.
- If memory increases in a loop, run the bundled tiny smoke and then compare the
  native context-release tests when they are safe to run.

## SVD / projection helper issues

- `get_2d_projection` and related helpers should not mutate the caller's
  array. If they appear to, confirm the input array was not reused elsewhere.
- Some methods allocate copies internally; a mutation complaint usually points
  to caller aliasing or a stale numpy view.

## Backend questions

- CPU importability does not prove CUDA/MPS/HPU runtime behavior.
- HPU users need `habana_frameworks.torch.core`; if absent, present it as a
  missing optional backend rather than a generic failure.
