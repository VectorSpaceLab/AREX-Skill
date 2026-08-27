# Dependency and Backend Guide

Use this guide before installing dependencies or running any Papers-in-100-Lines
implementation. The repository is a collection of standalone educational paper
scripts, not one installable Python package with a single dependency set.

## Repo-wide facts

- The source snapshot contains 62 paper implementation directories, 71 Python
  files, 63 README files, and per-paper `requirements.txt` files.
- There is no top-level `pyproject.toml`, `setup.py`, package module, or console
  entry point. Treat every paper directory as its own mini-project.
- Most entries use PyTorch, but versions range from old `torch==1.7.1` pins to
  recent `torch==2.7.0` pins. Several require specific CUDA-tagged wheels.
- Many entries also pin Keras, Torchvision, Pillow, Seaborn, Gym,
  Stable-Baselines3, Diffusers, Transformers, Safetensors, scikit-learn, or
  small specialty packages.
- Full scripts often write plots/images/frames and are training- or
  rendering-scale, not smoke tests.

## Environment strategy

1. **Choose exactly one paper or compatible family first.** Use the bundled
   implementation index or query helper.
2. **Create an isolated environment for that paper.** Do not install every
   requirements file into one environment.
3. **Install only selected requirements.** Preserve exact pins for full
   reproduction; loosen pins only for a documented adaptation after a tiny
   validation check.
4. **Treat CUDA as a real backend gate.** A CPU tensor check does not validate a
   CUDA-only script. Conversely, do not install GPU wheels for a catalog lookup
   or static adaptation task.
5. **Separate assets from code.** External data/weights/camera files and output
   directories should live in a scratch workspace, not inside the generated
   skill directory.

## Dependency families

| Family | Common requirements | Notes |
|---|---|---|
| Core educational scripts | `torch`, `numpy`, `matplotlib`, `tqdm` | Still isolate by paper because pins differ substantially. |
| Keras/MNIST examples | `keras`, sometimes `sklearn` or `seaborn` | Dataset loading may happen at import time. |
| Torchvision image datasets | `torchvision`, `pillow` | Can trigger dataset downloads and version conflicts with torch. |
| Diffusion/text-to-image | `transformers`, `diffusers`, `safetensors`, `Pillow` | Stable Diffusion and DreamBooth require external weights/tokenizers/images. |
| Reinforcement learning | `gym==0.23.1`, `stable_baselines3==1.2.0` | Atari environments also need ALE/ROM support and long training budgets. |
| Neural rendering and splatting | torch plus per-entry CUDA tags, image/data assets | Camera/ray/trained Gaussian assets are separate prerequisites. |

## Backend criticality in this generated skill

This generated skill was verified for static/source-inspection and bundled
helper workflows. Full paper reproduction is optional and unverified unless a
future user explicitly narrows to a paper, prepares its environment, supplies
assets, and approves runtime cost.

- Required for this skill: Python stdlib access to read the bundled catalog and
  run helper scripts.
- Optional for full upstream runs: CUDA, external model/data downloads, Atari
  ROMs, and long training/rendering budgets.
- Never convert an optional full-run skip into a claim that the paper result was
  reproduced.

## Safe validation ladder

Use the least expensive rung that answers the user request:

1. Catalog query and dependency/back-end plan.
2. Static inspection of classes/functions or distilled references.
3. Tiny synthetic shape test in a scratch file.
4. One or a few training/rendering updates with small tensors or images.
5. Full native paper script with exact requirements, data/weights, outputs,
   hardware, and budget approved.
