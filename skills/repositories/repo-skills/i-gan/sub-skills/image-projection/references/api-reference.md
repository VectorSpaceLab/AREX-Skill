# Image Projection API Reference

This reference captures the public command-line contract and the important
internal functions behind the iGAN image projection workflow. It is intended for
operating guidance, not as a replacement implementation.

## Command-Line Entry Point

Native script name:

```text
iGAN_predict.py
```

Documented command pattern:

```bash
THEANO_FLAGS='device=gpu0,floatX=float32,nvcc.fastmath=True' \
python iGAN_predict.py \
  --model_name shoes_64 \
  --input_image pics/shoes_test.png \
  --solver cnn_opt
```

Use the dry command builder for safe planning:

```bash
python sub-skills/image-projection/scripts/build_projection_command.py --help
```

## CLI Arguments

| Argument | Default | Meaning | Notes |
| --- | --- | --- | --- |
| `--model_name` | `shoes_64` | Name looked up in local DCGAN config. | Determines resolution, layers, feature count, and channels. |
| `--model_type` | `dcgan_theano` | Model backend module under `model_def`. | The projection workflow is Theano-specific in this repo. |
| `--input_image` | `pics/shoes_test.png` | Single image to project. | Opened with PIL/Pillow; resized internally. |
| `--output_image` | derived from input and solver | Reconstruction output image. | Literal `.png` replacement; use explicit paths for safety. |
| `--model_file` | `models/<model_name>.<model_type>` | Pickled packed model file. | Must match `model_name` configuration and include needed params. |
| `--solver` | `cnn_opt` | Projection solver: `cnn`, `opt`, or `cnn_opt`. | Source parser does not enforce choices; validate before runtime. |

## Default Path Derivation

If `--model_file` is omitted:

```text
model_file = './models/%s.%s' % (model_name, model_type)
```

If `--output_image` is omitted:

```text
output_image = input_image.replace('.png', '_%s.png' % solver)
```

Because the output rule uses literal replacement, an input such as
`photo.jpg` does not receive a new suffix. Provide `--output_image` for non-PNG
inputs or when accidental overwrite would be costly.

## Main Runtime Sequence

The native script performs these operations in order:

1. Parse arguments.
2. Fill default `model_file` and `output_image` values.
3. Print each argument key and value.
4. Open the input image with PIL/Pillow.
5. Locate `model_def.<model_type>` and instantiate `Model(..., use_predict=True)`.
6. Build inversion models with `def_invert_models(..., layer='conv4', alpha=0.002)`.
7. Resize the image to the generator's `npx` resolution.
8. Run `invert_images_CNN_opt(..., solver=<solver>)`.
9. Save the reconstructed image with PIL/Pillow.

## Important Internal Functions

| Function | Role | Key inputs | Key outputs |
| --- | --- | --- | --- |
| `def_feature(layer='conv4', up_scale=4)` | Builds AlexNet feature extractor. | Theano tensor image batch. | Theano function returning features for the selected layer. |
| `def_bfgs(model_G, layer='conv4', npx=64, alpha=0.002)` | Builds latent optimization objective. | Generator callable, feature layer, pixel size, feature-loss weight. | Theano function returning cost, gradient, generated image. |
| `def_predict(model_P)` | Builds feed-forward predictor. | Predictor network callable. | Theano function mapping image batch to latent `z`. |
| `def_invert_models(gen_model, layer='conv4', alpha=0.002)` | Creates all models required for projection. | Loaded generator model. | Tuple of generator, BFGS model, feature model, predictor model. |
| `predict_z(gen_model, _predict, ims, batch_size=32)` | Runs predictor over images. | Image batch in HWC format. | NumPy array of latent predictions. |
| `invert_bfgs_batch(...)` | Applies BFGS inversion image by image. | Generator, compiled optimizer, feature model, images, optional initial `z`. | Reconstructions, optimized latents, losses. |
| `invert_bfgs(...)` | Optimizes one image. | One-image batch, optional predicted `z`. | Generated image, optimized latent, final loss. |
| `invert_images_CNN_opt(...)` | Solver dispatcher. | Compiled models, image batch, solver string. | Reconstructions, optimized latents or `None`, predictor latents. |

## Tensor and Image Conventions

- CLI input image is read as HWC with PIL/Pillow.
- `gen_model.transform` converts HWC `[0,255]` images to NCHW float tensors in `[-1,1]` for RGB.
- The generator output is converted back to HWC RGB in `[0,1]`, then multiplied by 255 and cast to `uint8`.
- The latent dimension is hard-coded to 100 in the Theano DCGAN model class.
- The output image is resized back to the original PIL image dimensions before saving.

## Solver Internals

### `cnn`

`cnn` calls the trained predictor to estimate latent vectors, then generates
samples from those vectors. It does not run L-BFGS-B refinement.

Required runtime facts:

- DCGAN model file must include usable predictor weights.
- Predictor batchnorm data must be present.
- The predictor architecture must match the selected `model_name` config.

### `opt`

`opt` skips predictor initialization in the solver dispatcher and starts L-BFGS-B
from a random latent vector. However, the current setup still compiles the
predictor model before dispatching, so a model lacking predictor batchnorm can
fail before pure optimization begins.

Required runtime facts:

- Generator parameters and generator batchnorm must load.
- AlexNet `conv4` feature model must load.
- SciPy's L-BFGS-B optimizer must be available.
- The legacy Theano backend must compile the graph.

### `cnn_opt`

`cnn_opt` estimates an initial latent vector with `cnn`, then refines it through
L-BFGS-B. It is the documented default and usually the preferred quality path.

Required runtime facts:

- All `cnn` requirements.
- All `opt` requirements.

## AlexNet Feature Dependencies

The default projection feature layer is `conv4`. The AlexNet code builds layers
from `conv1` through `fc8` and loads a pickle named:

```text
models/caffe_reference_<layer>.pkl
```

For the default projection command, the required file is:

```text
models/caffe_reference_conv4.pkl
```

The source AlexNet preprocessing also requires:

```text
lib/ilsvrc_2012_mean.npy
```

It converts RGB iGAN tensors from `[-1,1]` to ImageNet-style BGR pixel values and
subtracts mean channel values.

## HOG Feature Notes

The optimization builder contains an internal branch for `layer == 'hog'`, but
the CLI does not expose a layer flag and the documented workflow uses AlexNet
`conv4`. The HOG module depends on Theano CUDA convolution and Python 2 era
relative import behavior. Treat HOG as a source-level extension point, not a
standard projection command option.

## Model Pickle Expectations

The Theano DCGAN model loader initializes parameter arrays and then fills them
from the model pickle. Relevant keys are:

```text
disc_params
gen_params
predict_params
disc_batchnorm
gen_batchnorm
predict_batchnorm
```

For projection, the generator keys are mandatory. For `cnn` and `cnn_opt`,
`predict_params` and `predict_batchnorm` must also be present and compatible.
Because the current projection setup compiles the predictor unconditionally, a
model without predictor batchnorm may also fail for `opt` unless the runtime code
is adjusted to build predictor functions only when needed.

## Native Candidate Preservation

Keep these native candidates for final verification planning:

| Candidate | Verification class | Expected signal |
| --- | --- | --- |
| `iGAN_predict.py --model_name shoes_64 --input_image pics/shoes_test.png --solver cnn_opt` | Optional CUDA/Theano/Lasagne/AlexNet/model case. | Writes a reconstruction image and prints final output path. |
| AlexNet planner for `conv4` | Skip-network URL evidence. | Reports `caffe_reference_conv4.pkl` URL and target without downloading. |

Do not run the native projection candidate unless the user has supplied or
approved the legacy runtime, model artifacts, AlexNet artifact, and GPU/backend
constraints.
