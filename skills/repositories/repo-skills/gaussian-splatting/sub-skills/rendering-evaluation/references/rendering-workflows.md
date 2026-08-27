# Rendering Workflows

## When To Read

Read this when a trained model should be rendered to PNG images, a pretrained model needs source-data overrides, or a model directory needs validation.

## Standard Render Flow

After training with `--eval`, render train/test sets:

```bash
python render.py -m <model>
```

Useful variants:

```bash
python render.py -m <model> --skip_train
python render.py -m <model> --skip_test
python render.py -m <model> --iteration 7000 --skip_train
```

`render.py` reads `cfg_args` from the model directory and merges command-line overrides. Parameters such as `--source_path`, `--images`, `--eval`, `--resolution`, `--white_background`, `--train_test_exp`, `--convert_SHs_python`, `--convert_cov3D_python`, and `--antialiasing` can be overridden on the command line.

## Pretrained Model Flow

For pretrained models, provide the corresponding source dataset explicitly if it is not encoded in a usable `cfg_args` path:

```bash
python render.py -m <pretrained-model> -s <COLMAP-or-Blender-scene>
```

Then compute metrics:

```bash
python metrics.py -m <pretrained-model>
```

The README warns that pretrained models were created with release code and metrics may differ from paper numbers after cleanup/bugfixes.

## Output Layout

`render.py` writes:

```text
<model>/train/ours_<iteration>/renders/*.png
<model>/train/ours_<iteration>/gt/*.png
<model>/test/ours_<iteration>/renders/*.png
<model>/test/ours_<iteration>/gt/*.png
```

Use `scripts/validate_model_outputs.py` to inspect the model/render layout without running CUDA:

```bash
python validate_model_outputs.py --model-root <model> --iteration 30000
# If render.py used --skip_train, require only the test split:
python validate_model_outputs.py --model-root <model> --iteration 30000 --skip-train
```

## Rendering Details

- `render.py` loads the latest saved iteration when `--iteration -1` is used.
- It uses `GaussianModel(dataset.sh_degree)` and `Scene(..., load_iteration=iteration, shuffle=False)`.
- Background is black by default or white with `--white_background`.
- It saves both rendered images and ground-truth images for the selected train/test cameras.
- If `--train_test_exp` is active, rendering and GT tensors are sliced to use the right half for evaluation.

## Backend Requirements

Offline rendering uses CUDA tensors and the differentiable rasterizer. Do not treat output-layout validation as proof that rendering itself works. Verify the backend with the setup-and-backends sub-skill before running render commands.
