---
name: model-inference
description: "Set up iGAN pretrained DCGAN artifacts, choose model zoo entries,
  build sample-generation commands, and use dcgan_theano.Model API facts
  safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# model-inference

Use this sub-skill when the task is about loading or selecting iGAN pretrained
DCGAN models, planning model artifact downloads, building the standalone sample
command, or understanding the `dcgan_theano.Model` inference API without opening
the source checkout.

## Route here

- Choose among the iGAN pretrained DCGAN model zoo entries.
- Plan where a `*.dcgan_theano` model file should live before running iGAN.
- Build a safe command for random sample generation from a pretrained model.
- Diagnose missing model artifacts before launching GPU/Theano code.
- Explain `dcgan_theano.Model` construction, generation, transforms, and output
  shapes.
- Preserve model URL and target-path evidence without performing network access.

## Route elsewhere

- Interactive PyQt4 drawing, sliders, candidate panes, ShadowDraw UI, or launch
  flags belong in [interactive-ui](../interactive-ui/SKILL.md).
- Color-map, mask, edge-map, or headless constrained generation workflows belong
  in [constraint-generation](../constraint-generation/SKILL.md).
- Image-to-latent projection, AlexNet artifacts, `cnn`, `opt`, or `cnn_opt`
  solvers belong in [image-projection](../image-projection/SKILL.md).
- Dataset creation, HDF5 files, DCGAN training, batchnorm estimation, predictor
  training, and model packing belong in [training-data](../training-data/SKILL.md).

## Core facts

- The inference model type used by this repo is `dcgan_theano`.
- The default model file convention is `./models/<model_name>.dcgan_theano`.
- The sample workflow emits a grid image, defaulting to
  `<model_name>_dcgan_theano_samples.png`.
- The documented sample run generates `196` images in batches of `49`, then
  arranges them as a `14 x 14` grid.
- Full native execution assumes a legacy Python2-era Theano CUDA/cuDNN stack plus
  OpenCV and a downloaded model file. Command building and URL planning are safe
  dry-run operations and do not validate GPU execution.
- All bundled scripts in this sub-skill are side-effect safe by default: they do
  not import Theano, train models, use a GPU, or download files.

## Model zoo names

Use one of these canonical pretrained names unless you intentionally add a new
compatible config and model artifact:

| Model name | Channels | Notes |
| --- | ---: | --- |
| `outdoor_64` | 3 | 64x64 landscape model. |
| `church_64` | 3 | 64x64 LSUN church model. |
| `handbag_64` | 3 | 64x64 handbag model. |
| `shoes_64` | 3 | 64x64 shoe-photo model. |
| `hed_shoes_64` | 1 | 64x64 shoe-sketch/HED model; often paired with UI shadow mode. |

For architecture and transform details, read
[references/api-reference.md](references/api-reference.md). For model setup and
sample workflows, read [references/model-workflows.md](references/model-workflows.md).

## Standard workflow

1. Select the model name from the model zoo.
2. Use the artifact planner to confirm the public URL and expected target path.
3. Download or stage the model artifact outside the helper if network access and
   storage are explicitly allowed.
4. Build the sample-generation command using the command builder.
5. If a legacy runtime is available, run the generated command with appropriate
   `THEANO_FLAGS`; otherwise keep the command as a reproducible handoff.
6. If native execution fails, consult
   [references/troubleshooting.md](references/troubleshooting.md) and the root
   troubleshooting reference when the issue is cross-cutting.

## Bundled helpers

- `scripts/igan_artifact_urls.py` prints the model artifact URL, expected target
  path, optional preview-sample URLs, and a missing/present status check. It does
  not download or modify files.
- `scripts/build_model_command.py` prints a reproducible command and environment
  plan equivalent to the standalone sample script. It can also report whether
  the planned model file is currently present.

Example dry plan for a missing artifact:

```bash
python sub-skills/model-inference/scripts/igan_artifact_urls.py outdoor_64 --check-existing
```

Example dry sample command with explicit paths:

```bash
python sub-skills/model-inference/scripts/build_model_command.py \
  --model_name shoes_64 \
  --model_file models/shoes_64.dcgan_theano \
  --output_image outputs/shoes_grid.png \
  --check-model
```

## Validation signals

A healthy dry-run handoff includes:

- `model_name` matches a known model-zoo/config entry or the user explicitly
  allowed a custom name.
- `model_type` is `dcgan_theano` unless the task is about extending the backend.
- The model target ends with `.dcgan_theano` and follows the default convention
  unless a custom file is supplied.
- The command includes `THEANO_FLAGS` for GPU use or clearly states that flags
  were intentionally omitted.
- `--check-model` reports `present` before actual generation, or reports
  `missing` with the artifact planner command needed to obtain the URL.

## Native execution caveat

The original sample workflow is a valuable native verification candidate, but it
is not a safe default check. It imports Theano, compiles a generator, loads a
pickle-like model file, uses CUDA/cuDNN in the documented setup, imports OpenCV,
and writes an image. Treat successful dry command generation as static planning,
not proof that the legacy model can run on the current machine.

## Troubleshooting first steps

- Missing model file: run the artifact planner and stage the exact
  `<model_name>.dcgan_theano` target.
- Unknown model name: compare with the model zoo table and the config table in
  [references/api-reference.md](references/api-reference.md).
- Import or compile failures: check the legacy stack matrix in
  [references/troubleshooting.md](references/troubleshooting.md).
- Color/channel surprises for `hed_shoes_64`: verify that downstream workflows
  expect a one-channel model and route UI shadow behavior to the UI sub-skill.

## Output contract for future agents

When asked to produce a model-inference handoff, return the chosen model name,
model type, planned model file, artifact URL and target, command/env plan,
expected output image, whether the file exists, whether native execution was
actually attempted, and unresolved runtime blockers. Do not claim a download,
GPU compile, or sample image was produced unless that command was explicitly run
and verified.
