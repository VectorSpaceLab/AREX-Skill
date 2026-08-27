---
name: image-projection
description: "Project an image into iGAN latent space and reconstruct it with
  iGAN_predict.py, safe command builders, AlexNet planning, and projection
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# iGAN Image Projection Router

Use this sub-skill when the task is to project a real image into the latent
space of an iGAN DCGAN model and save the reconstructed image.

This router covers the `iGAN_predict.py` workflow, the solver choices
`cnn`, `opt`, and `cnn_opt`, the AlexNet `conv4` feature dependency used by the
published command, and the model-file requirements for predictor parameters.

Do not use this sub-skill for random sampling, downloading DCGAN model-zoo
artifacts, interactive editing, non-UI constraint maps, or training the
predictor network. Route those tasks to sibling skills instead.

## Read First

- Projection workflow recipes: [references/projection-workflows.md](references/projection-workflows.md)
- CLI and internal API facts: [references/api-reference.md](references/api-reference.md)
- Projection failure modes: [references/troubleshooting.md](references/troubleshooting.md)
- Dry projection command builder: [scripts/build_projection_command.py](scripts/build_projection_command.py)
- AlexNet URL/target planner: [scripts/igan_alexnet_urls.py](scripts/igan_alexnet_urls.py)

## When To Use

Use this sub-skill for tasks such as:

- Build the exact `iGAN_predict.py` command for a given input image.
- Choose between `cnn`, `opt`, and `cnn_opt` projection solvers.
- Explain where the output reconstruction image will be written.
- Preflight required artifacts for projection without running Theano.
- Plan the AlexNet `conv4` pickle target without performing a download.
- Diagnose missing AlexNet, missing DCGAN model files, or predictor-param errors.

## Route Elsewhere

- Random sample grids or DCGAN model-zoo setup: use [../model-inference/SKILL.md](../model-inference/SKILL.md).
- Predictor training, HDF5 datasets, batchnorm refresh, or model packing: use [../training-data/SKILL.md](../training-data/SKILL.md).
- Color, mask, edge, or sketch constraints for headless generation: use [../constraint-generation/SKILL.md](../constraint-generation/SKILL.md).
- Interactive PyQt4 drawing workflows: use [../interactive-ui/SKILL.md](../interactive-ui/SKILL.md).

## Projection Preconditions

Projection is a legacy native workflow. Before proposing a runtime run, confirm:

1. The user has an iGAN runtime checkout or equivalent files containing `iGAN_predict.py`.
2. The Python environment can import Theano, Lasagne, NumPy, SciPy, PIL/Pillow, and iGAN local modules.
3. The intended backend is compatible with old Theano CUDA/cuDNN expectations, or the user accepts a slow/experimental CPU attempt.
4. The DCGAN model file exists at `models/<model_name>.<model_type>` or the user supplies `--model_file`.
5. The model file includes generator parameters and, for the current projection script, predictor parameters and predictor batchnorm arrays.
6. The AlexNet feature pickle exists at `models/caffe_reference_conv4.pkl` for the default feature layer.
7. The input image is readable by PIL/Pillow; the script resizes it internally to the model resolution and then back to the original dimensions.

If any runtime artifact is missing, use the bundled dry-run helpers and references
instead of attempting a native GPU run.

## Safe Command Construction

For most tasks, first build a dry command:

```bash
python sub-skills/image-projection/scripts/build_projection_command.py \
  --model-name shoes_64 \
  --input-image pics/shoes_test.png \
  --solver cnn_opt
```

For a custom pure optimization command with an explicit output path:

```bash
python sub-skills/image-projection/scripts/build_projection_command.py \
  --model-name shoes_64 \
  --input-image inputs/shoe.png \
  --solver opt \
  --output-image outputs/shoe_opt.png
```

The helper prints a command only. It never imports Theano, opens images, uses a
GPU, starts training, or downloads files.

## AlexNet Artifact Planning

The documented projection command uses AlexNet `conv4` features. Plan the URL
and local target without network side effects:

```bash
python sub-skills/image-projection/scripts/igan_alexnet_urls.py --layer conv4
```

The planner only reports URLs and expected targets. It does not download
AlexNet, DCGAN models, or predictor parameters.

## Native Runtime Command Pattern

When all artifacts and the legacy runtime are available, the command pattern is:

```bash
THEANO_FLAGS='device=gpu0,floatX=float32,nvcc.fastmath=True' \
python iGAN_predict.py \
  --model_name shoes_64 \
  --input_image pics/shoes_test.png \
  --solver cnn_opt
```

If `--output_image` is omitted and the input filename contains `.png`, the
script writes beside the input as `<input_stem>_<solver>.png`. For example,
`pics/shoes_test.png` with `cnn_opt` becomes `pics/shoes_test_cnn_opt.png`.

## Solver Selection

- `cnn`: fastest feed-forward projection through the trained predictor network; requires usable predictor params.
- `opt`: L-BFGS-B latent optimization against pixel and feature reconstruction losses; slower and still compiled through the current predictor-aware setup.
- `cnn_opt`: default hybrid; starts from the predictor and refines with L-BFGS-B; best documented quality.

Prefer `cnn_opt` unless the user explicitly requests speed (`cnn`) or a custom
optimization baseline (`opt`). Reject unknown solver strings before runtime; the
source script does not validate them robustly.

## Output Contract

A successful run prints parsed arguments, reads one image, compiles Theano
functions, loads the model and AlexNet feature network, reconstructs one image,
and saves the result to `--output_image` or the default solver-suffixed PNG path.

The output image is a reconstructed RGB image resized back to the original input
dimensions. The script does not save the optimized latent vector by default.

## Validation Checklist

Before telling a user a projection is ready to run, verify or explicitly mark unknown:

- `iGAN_predict.py` is available in the working runtime checkout.
- `models/<model_name>.<model_type>` or the supplied `--model_file` exists.
- `models/caffe_reference_conv4.pkl` exists for the default projection path.
- `lib/ilsvrc_2012_mean.npy` exists with the local iGAN library files.
- The input image path exists and is a PIL-readable image.
- The environment has Theano/Lasagne/SciPy/PIL and a backend acceptable to the user.
- The model contains predictor params if using `cnn` or `cnn_opt`, and preferably even for `opt` because the original script compiles the predictor unconditionally.

## Troubleshooting Entry Points

If native execution fails, classify the symptom first:

- Import errors or syntax/runtime incompatibilities: see [references/troubleshooting.md](references/troubleshooting.md#legacy-python-and-import-failures).
- Missing files or wrong targets: see [references/troubleshooting.md](references/troubleshooting.md#artifact-and-path-failures).
- Predictor-param or solver problems: see [references/troubleshooting.md](references/troubleshooting.md#solver-and-predictor-failures).
- Theano/CUDA/cuDNN compile failures: see [references/troubleshooting.md](references/troubleshooting.md#theano-cuda-and-cudnn-failures).

## Boundary Reminders

Keep this sub-skill focused on image projection only. It may refer to DCGAN model
files and predictor parameters as required inputs, but it does not own model-zoo
downloads, predictor training, or model packing. It may mention AlexNet `conv4`
because the projection loss depends on it, but network downloads must remain a
manual user action planned by the bundled URL helper.
