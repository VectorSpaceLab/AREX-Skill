---
name: zi2zi
description: "Operate zi2zi legacy Chinese/Japanese/Korean font style transfer
  workflows: paired glyph data preparation, TensorFlow 1.x training, inference,
  interpolation, and generator export."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# zi2zi

Use this repo skill when a task is about **zi2zi**, the legacy TensorFlow 1.x
conditional GAN for Chinese, Japanese, Korean, or other font style transfer.
The skill is a router plus compact operating context; read the linked
sub-skills for concrete commands, data formats, validation checks, and
troubleshooting.

## Use this skill when

- The user wants to create zi2zi training data from source/target fonts.
- The user has glyph pair JPGs and needs `train.obj` / `val.obj` files.
- The user wants to train or fine-tune zi2zi's conditional adversarial U-Net.
- The user wants to run generator inference, interpolate between style labels,
  create transition frames/GIFs, or export generator weights.
- The user needs help debugging legacy Python 2.7, TensorFlow 1.x, Pillow,
  scipy image I/O, checkpoint, label, or experiment-layout problems in a zi2zi
  workflow.

## Avoid this skill when

- The task is a general pix2pix, CycleGAN, diffusion, OCR, or font-rendering
  question with no zi2zi command/API surface.
- The user is asking to port zi2zi to TensorFlow 2/PyTorch; this skill can
  explain the legacy model but does not provide a porting recipe.
- The user needs a modern packaged library with importable Python APIs; zi2zi is
  primarily a script-based repository, not an installable distribution.

## Runtime expectations

For freshness checks, read [repo provenance](references/repo-provenance.md)
before using this skill against a different zi2zi checkout.

- zi2zi is legacy **Python 2.7 + TensorFlow 1.x** code. Do not assume Python 3,
  TensorFlow 2, or current `scipy.misc` APIs work with the original scripts.
- Practical training and checkpoint inference were designed for CUDA/cuDNN, but
  full training is long-running and should not be launched without explicit user
  approval, data, output location, and hardware budget.
- No pretrained checkpoint or font files are bundled in this skill. When a task
  needs real training or inference, confirm the user has source/target fonts,
  packaged `.obj` data, or a TensorFlow checkpoint.
- The bundled scripts in this skill are safe Python 3 planners/inspectors. They
  help construct commands and validate artifacts; they are not replacements for
  zi2zi's full TensorFlow model implementation.

## Public install and verification direction

Use an isolated legacy environment for the original zi2zi scripts. A typical
Conda direction is:

```sh
conda create -n zi2zi-legacy python=2.7 pip
conda install -n zi2zi-legacy tensorflow-gpu=1.15 scipy imageio pillow functools32
```

Then verify parser/import readiness from a zi2zi checkout:

```sh
python font2img.py --help
python package.py --help
python train.py --help
python infer.py --help
python export.py --help
```

Do not run long training or checkpoint inference until the user confirms data,
checkpoint paths, GPU/runtime readiness, and output locations.

## Route map

| If the task is about... | Read |
| --- | --- |
| Rendering paired glyph images, choosing CJK/custom charsets, label prefixes, packaging JPGs into `.obj`, or inspecting packaged data | [data-preparation](sub-skills/data-preparation/SKILL.md) |
| Training or fine-tuning, experiment directories, losses, label shuffling, `freeze_encoder`, `fine_tune`, checkpoints, samples, or model architecture | [training-and-model](sub-skills/training-and-model/SKILL.md) |
| Generator inference, random style IDs, interpolation frames/GIFs, output image names, checkpoint restore, or generator-only export | [inference-and-export](sub-skills/inference-and-export/SKILL.md) |
| End-to-end flow across all stages | [workflow overview](references/workflow-overview.md) |
| Legacy dependency and backend compatibility | [compatibility](references/compatibility.md) |
| Cross-cutting failures that affect multiple stages | [troubleshooting](references/troubleshooting.md) |

## Standard end-to-end flow

1. Use `font2img.py` semantics to render source/target glyph pairs. The target
   glyph occupies the left half of each JPG, the source glyph the right half,
   and the filename prefix stores the style label.
2. Use `package.py` semantics to create `train.obj` and `val.obj`, each a stream
   of pickled `(label, image_bytes)` records.
3. Place those files under an experiment data directory, normally
   `experiment/data/train.obj` and `experiment/data/val.obj`.
4. Train with `train.py`, which creates per-experiment checkpoint, log, and
   sample directories and saves checkpoints under a batch-size-specific name.
5. Run `infer.py` from a trained generator checkpoint, optionally interpolating
   style embeddings and compiling frames into a GIF.
6. Use `export.py` only when a generator-only checkpoint is needed for later
   inference or transfer.

## Useful bundled helpers

- Run [scripts/zi2zi_smoke_plan.py](scripts/zi2zi_smoke_plan.py) when you need a
  safe checklist of zi2zi files, dependencies, and native smoke commands for a
  user's checkout.
- Use the data-preparation planners before writing or executing destructive
  preprocessing commands.
- Use the training and inference planners to validate paths, labels, and
  command flags before launching long TensorFlow jobs.

## Verification baseline

During skill construction, safe checks covered Python 2.7 dependency imports,
all five original script `--help` parsers, and a CPU-hidden TensorFlow 1.15
`UNet` graph build. Full CUDA training and checkpoint-backed inference/export
were intentionally not run because they require user-provided fonts/data or
checkpoints and a legacy CUDA runtime budget. Preserve that distinction when
answering runtime-readiness questions.
