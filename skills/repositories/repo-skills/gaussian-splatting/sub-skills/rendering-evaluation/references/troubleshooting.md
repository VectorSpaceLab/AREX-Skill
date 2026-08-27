# Rendering and Evaluation Troubleshooting

## `Config file not found at .../cfg_args`

`render.py` could not read the saved training config from the model directory.

Fix:

- Confirm `-m/--model_path` points at the trained model root, not an iteration subfolder.
- Provide explicit `-s/--source_path`, `--images`, `--eval`, and related options when evaluating a portable/pretrained model.
- Validate the model directory with `scripts/validate_model_outputs.py --model-root <model>`.

## Missing `point_cloud/iteration_*/point_cloud.ply`

Rendering loads a trained Gaussian point cloud from `point_cloud/iteration_<N>/point_cloud.ply`.

Fix:

- Check that training completed or saved the desired iteration.
- Use `--iteration <N>` if the latest iteration is not the desired one.
- Do not point `render.py` at `point_cloud/iteration_<N>` directly; pass the model root.

## Metrics Prints `Unable to compute metrics for model ...`

The metrics script catches broad exceptions and prints this message. Common causes:

- Missing `<model>/test/ours_<N>/renders` or `gt` directories.
- No test split was rendered.
- PNG file names do not match between `renders` and `gt`.
- LPIPS/torchvision weights or CUDA are unavailable.

Fix:

1. Validate the output layout.
2. Render the test split without `--skip_test`.
3. Confirm CUDA and LPIPS dependencies are available.

## LPIPS / Torchvision Weight Downloads

The bundled LPIPS code constructs a VGG network for `metrics.py`. In a fresh environment, torchvision may try to access cached weights. Do not trigger network downloads without user approval. If weights are unavailable, record metrics as blocked/skipped or use only already-generated metric files.

LPIPS with VGG also expects images large enough to survive the network's pooling layers. Very tiny smoke-test images can make metrics print `Unable to compute metrics for model ...` even when render folders exist. Use realistic image sizes for metrics smoke tests.

## Pretrained Model Source Path Is Invalid

A pretrained model's `cfg_args` may point to the authors' original source location. Override it:

```bash
python render.py -m <pretrained-model> -s <local-source-scene>
```

Make sure the source scene has matching cameras/images for that model.

## Full Evaluation Is Too Slow

`full_eval.py` can take hours and requires large datasets. For verification or planning, generate the command and explain inputs instead of running it. Run the full benchmark only when the user explicitly approves compute, dataset availability, and expected runtime.

## Antialiasing or Exposure Mismatch

If a model was trained with `--antialiasing` or `--train_test_exp`, carry matching flags into render/evaluation commands when overriding config. Mismatched flags can change images or split handling.
