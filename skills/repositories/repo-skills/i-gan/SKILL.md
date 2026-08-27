---
name: i-gan
description: "Operate the legacy iGAN repository for interactive GAN image
  generation, constrained synthesis, image projection, model artifacts, and
  DCGAN training workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# i-gan

Use this repo skill when a task involves the iGAN / Interactive GAN codebase for
GAN-based image generation, visual manipulation on the image manifold, legacy
Theano DCGAN models, PyQt4 interaction, constraint-map synthesis, latent
projection, or training iGAN-style DCGAN artifacts.

This skill is intentionally self-contained: use the bundled references and
helpers here instead of reopening the original README or shell scripts. The
helpers are dry-run planners and validators by default; they do not download
large artifacts, import Theano/PyQt4, train models, launch a GUI, or use a GPU.

## Fast route map

| User task | Read this |
| --- | --- |
| Download-plan a pretrained model, choose model zoo names, build random sample commands, or inspect `dcgan_theano.Model` facts | [sub-skills/model-inference/SKILL.md](sub-skills/model-inference/SKILL.md) |
| Generate images from color, mask, and edge constraints without the GUI | [sub-skills/constraint-generation/SKILL.md](sub-skills/constraint-generation/SKILL.md) |
| Launch or explain the interactive drawing UI, controls, shortcuts, ShadowDraw, or AverageExplorer | [sub-skills/interactive-ui/SKILL.md](sub-skills/interactive-ui/SKILL.md) |
| Project an input image into latent space using `cnn`, `opt`, or `cnn_opt` solvers | [sub-skills/image-projection/SKILL.md](sub-skills/image-projection/SKILL.md) |
| Plan datasets, HDF5 creation, DCGAN training, batchnorm, predictor training, packing, or custom model configs | [sub-skills/training-data/SKILL.md](sub-skills/training-data/SKILL.md) |

## Setup / installation stance

The repository does not publish package metadata for `pip install`; operate it
as a script checkout with repo-local modules. If a user asks for installation,
clone or unpack the iGAN source, stage workflow-specific artifacts, and prepare
only the legacy dependencies required by the chosen route. The minimal safe
verification command is the bundled preflight helper below, not a Theano import.

## What to verify first

1. Read [references/repo-provenance.md](references/repo-provenance.md) when
   deciding whether this skill matches the current checkout.
2. Run the checkout preflight helper before native execution:

   ```bash
   python scripts/check_igan_checkout.py --repo-root <iGAN-checkout> --format text
   ```

3. If the task asks to run generation, UI, projection, or training, confirm that
   the user has explicitly supplied or authorized the legacy runtime, model/data
   artifacts, and hardware/display requirements listed below.
4. Use the nearest sub-skill helper to build a command or validate inputs before
   launching original heavy code.

## Runtime reality check

The original repository is a legacy script-based project, not an installable
Python package. Its native workflows assume a Python2-era stack with Theano,
CUDA/cuDNN, OpenCV, PyQt4/qdarkstyle for the UI, Lasagne/SciPy/PIL for
projection, and Fuel/h5py/tqdm for training/data preparation. Modern Python and
modern CUDA hosts often need compatibility work. Do not treat static helper
success as proof that native Theano execution works.

The bundled helpers are safe for planning and validation:

- [scripts/check_igan_checkout.py](scripts/check_igan_checkout.py) inspects a
  checkout for expected source files, optional artifact files, GPU/display
  signals, and likely blockers without importing repo modules.
- Sub-skill command builders construct reproducible shell commands and
  `THEANO_FLAGS` plans without executing them.
- URL planners print artifact URLs and target paths without downloading.
- Input validators inspect file presence and lightweight image headers without
  requiring OpenCV.

## Common operating sequence

1. Identify the intended workflow and load the matching sub-skill.
2. Run or read the sub-skill helper to produce a dry command/data/artifact plan.
3. Check [references/troubleshooting.md](references/troubleshooting.md) for
   cross-cutting dependency, model, display, and backend failures.
4. Stage any model, AlexNet, or dataset artifacts only after network and disk
   use are approved.
5. If a compatible legacy runtime exists, run the generated command and record
   whether native execution actually happened.
6. If native execution is unavailable, return a precise handoff: command plan,
   missing artifacts/dependencies/backends, and the sub-skill references used.

## When not to use this skill

- Use a modern Diffusers/Stable Diffusion/ComfyUI skill when the task is about
  diffusion pipelines, LoRA, schedulers, or node graphs rather than this iGAN
  Theano codebase.
- Use a generic computer-vision or PyTorch training skill when the user is not
  specifically working with iGAN-style DCGAN scripts or artifacts.
- Do not use this skill as proof of native runtime verification; it provides
  operating guidance and safe preflight helpers unless a legacy environment is
  separately prepared and tested.

## Output contract

When handing work back to a user or another agent, include the selected route,
model/dataset/artifact names, command or validation plan, artifact status,
whether any native command was actually run, the expected outputs, and remaining
legacy runtime blockers. Never claim that downloads, GPU compilation, UI launch,
training, or image generation occurred unless those commands were explicitly run
and their outputs were checked.
