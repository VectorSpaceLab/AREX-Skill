# Projection Workflows

This reference gives self-contained operating steps for projecting one image into
iGAN latent space and saving its reconstruction. Use it together with the safe
helper [../scripts/build_projection_command.py](../scripts/build_projection_command.py)
and the AlexNet planner [../scripts/igan_alexnet_urls.py](../scripts/igan_alexnet_urls.py).

## Workflow Summary

The projection path is `x -> z -> reconstruction`:

1. Read one input image with PIL/Pillow.
2. Load a DCGAN Theano model such as `shoes_64.dcgan_theano`.
3. Compile the generator, predictor, AlexNet feature extractor, and L-BFGS-B objective.
4. Resize the image to the model resolution, usually 64 x 64.
5. Use the selected solver to estimate latent `z`.
6. Generate a reconstruction and resize it back to the input image dimensions.
7. Save the output PNG.

The native script is designed for one image at a time. Batch helper functions
exist internally, but the command-line entry point opens one `--input_image` and
writes one `--output_image`.

## Dry-Run First

Build a command before executing native Theano code:

```bash
python sub-skills/image-projection/scripts/build_projection_command.py \
  --model-name shoes_64 \
  --input-image pics/shoes_test.png \
  --solver cnn_opt
```

Expected dry-run output is a shell command similar to:

```bash
THEANO_FLAGS=device=gpu0,floatX=float32,nvcc.fastmath=True python iGAN_predict.py --model_name shoes_64 --model_type dcgan_theano --input_image pics/shoes_test.png --solver cnn_opt
```

The command builder does not check that the files exist unless asked by a caller
to do separate filesystem checks. Its main purpose is preserving the source CLI
contract without importing Theano or using a GPU.

## Common Native Projection Command

When the legacy runtime, model, image, and AlexNet feature file are present:

```bash
THEANO_FLAGS='device=gpu0,floatX=float32,nvcc.fastmath=True' \
python iGAN_predict.py \
  --model_name shoes_64 \
  --input_image pics/shoes_test.png \
  --solver cnn_opt
```

The documented sample input is an RGB PNG of size 136 x 102. The script resizes
it to the model's square resolution for inference and resizes the reconstruction
back to the input size before saving.

## Custom Output Path

Always use `--output_image` when the input is not a PNG or when overwriting next
to the source image would be risky:

```bash
python sub-skills/image-projection/scripts/build_projection_command.py \
  --model-name shoes_64 \
  --input-image inputs/shoe-photo.png \
  --solver opt \
  --output-image outputs/shoe-photo_opt.png
```

Native command pattern:

```bash
THEANO_FLAGS='device=gpu0,floatX=float32,nvcc.fastmath=True' \
python iGAN_predict.py \
  --model_name shoes_64 \
  --input_image inputs/shoe-photo.png \
  --solver opt \
  --output_image outputs/shoe-photo_opt.png
```

If `--output_image` is omitted, the source code computes:

```text
output_image = input_image.replace('.png', '_<solver>.png')
```

That is a literal string replacement. For a non-PNG filename, the output may be
identical to the input path. Prefer explicit output paths for JPEGs or unusual
filenames.

## Required Artifacts

Projection needs two different model artifact families:

| Artifact | Default target | Why it is needed |
| --- | --- | --- |
| DCGAN model | `models/<model_name>.<model_type>` | Supplies generator parameters and model resolution/configuration. |
| Predictor params inside the DCGAN pickle | same model file | Used by `cnn` and `cnn_opt`; the current script also compiles the predictor during setup. |
| AlexNet feature pickle | `models/caffe_reference_conv4.pkl` | Supplies feature-network parameters for the default `conv4` feature loss. |
| ImageNet mean file | `lib/ilsvrc_2012_mean.npy` | Used by AlexNet image preprocessing. |

The AlexNet planner reports the URL and target for `conv4` without downloading:

```bash
python sub-skills/image-projection/scripts/igan_alexnet_urls.py --layer conv4
```

Important distinction: the AlexNet pickle is not the DCGAN predictor. If a model
file lacks `predict_params` or `predict_batchnorm`, downloading AlexNet does not
fix `cnn` or `cnn_opt` predictor failures. The predictor belongs inside the
packed DCGAN model and is produced by the training/data lifecycle.

## Solver Guidance

| Solver | Behavior | Choose it when | Main requirements |
| --- | --- | --- | --- |
| `cnn` | Feed-forward predictor estimates `z`, then generator reconstructs. | Speed matters more than refinement. | Trained predictor params and batchnorm in the DCGAN model. |
| `opt` | L-BFGS-B directly optimizes `z` against pixel and feature losses. | Comparing against a pure optimization baseline. | Generator, AlexNet feature network, SciPy optimizer; current setup still compiles predictor. |
| `cnn_opt` | Predictor initialization followed by L-BFGS-B refinement. | Default high-quality projection. | Both predictor and optimization dependencies. |

Reject unknown solver values before running. The original CLI accepts any string,
but the downstream function only handles the three documented solvers.

## Model File Selection

Defaults:

```text
--model_name shoes_64
--model_type dcgan_theano
--model_file models/shoes_64.dcgan_theano
```

Use `--model_file` when the model is stored elsewhere or when testing a custom
packed model:

```bash
python sub-skills/image-projection/scripts/build_projection_command.py \
  --model-name shoes_64 \
  --model-file models/custom_shoes_with_predictor.dcgan_theano \
  --input-image pics/shoes_test.png \
  --solver cnn_opt
```

The `model_name` still matters because the local model configuration determines
image resolution, number of layers, feature count, and channel count.

## AlexNet Layer Notes

The published projection workflow uses `conv4`. The AlexNet module also contains
network branches for `conv1`, `conv2`, `conv3`, `conv5`, `fc6`, `fc7`, and `fc8`,
but `iGAN_predict.py` does not expose a CLI flag to change the layer. Treat
non-`conv4` layers as advanced code-modification territory unless a user is
already maintaining a custom projection script.

The internal `hog` branch is not exposed by the CLI either. It depends on a
Theano CUDA convolution path and has Python 2 style relative imports; use it only
when debugging a custom fork that intentionally changes the feature layer.

## Minimal Preflight Procedure

Before a native run, ask or check:

```text
[ ] Input image exists and PIL/Pillow can open it.
[ ] Model file exists at the planned `--model_file`.
[ ] Model file is known to include `predict_params` and `predict_batchnorm`.
[ ] `models/caffe_reference_conv4.pkl` exists.
[ ] `lib/ilsvrc_2012_mean.npy` exists.
[ ] Python runtime can import Theano, Lasagne, SciPy, NumPy, and PIL/Pillow.
[ ] Theano backend flags match available hardware.
[ ] The output path is explicit or the default PNG suffix behavior is acceptable.
```

If any item is unknown, use the dry-run helpers and report the gap instead of
claiming the native projection is verified.

## Expected Runtime Signals

Successful native execution prints argument values, reads the image dimensions,
prints `COMPILING...` for several Theano functions, loads the model, reports
optimization iterations for `opt` or `cnn_opt`, then prints:

```text
write result to <output_image>
```

The reconstruction is saved as an image file. The native CLI does not save `z`,
loss curves, AlexNet features, or intermediate resized images.

## What Not To Do Here

- Do not start DCGAN model downloads; route model-zoo setup to the model-inference sub-skill.
- Do not train or pack predictor networks; route predictor lifecycle work to the training-data sub-skill.
- Do not construct color/mask/edge constraints; route those to the constraint-generation sub-skill.
- Do not run the PyQt4 UI just to project an image; projection is a separate CLI workflow.
