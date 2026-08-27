# Repo-Level Troubleshooting

Use this reference for failures that cut across several Papers-in-100-Lines
families. For algorithm-specific issues, follow the nearest sub-skill's
troubleshooting reference.

## The repository is not installable as one package

Symptoms: `pip install -e .` fails, no package metadata is found, or no import
module named after the repository exists.

Recovery:

- Treat the repo as a catalog of standalone paper mini-projects.
- Use the bundled implementation index to select a paper and its per-directory
  requirements.
- Do not expect console entry points or a single import namespace.

## Installing all requirements breaks the environment

Symptoms: resolver conflicts, incompatible torch/torchvision pins, Keras version
errors, or CUDA ABI mismatches.

Recovery:

1. Select one paper first.
2. Create a fresh environment for that paper or compatible small subset.
3. Install only that paper's requirements and the matching framework backend.
4. Keep catalog/static tasks on the stdlib helper path with no ML dependency
   install.

## A full script starts expensive work

Symptoms: a script begins long training, rendering hundreds of frames, emulator
interaction, or 1,000-step sampling.

Recovery:

- Stop the run if cost was not approved.
- Use the owning sub-skill to create a reduced tiny adaptation.
- Estimate loop size or rendering memory with bundled helpers before retrying.

## Network, datasets, or model weights are missing

Symptoms: Keras/Torchvision/Transformers downloads, missing Google Drive data,
missing `v1-5-pruned-emaonly.safetensors`, missing trained Gaussian tensors, or
missing Atari ROMs.

Recovery:

- Ask for approval before downloading. Record source, size, license, and cache
  policy.
- Use synthetic fixtures for debugging shapes when full data is not required.
- Do not store downloaded assets inside the generated skill directory.

## CUDA/backend problems

Symptoms: `Torch not compiled with CUDA enabled`, `no kernel image`, device
mismatch, unavailable GPU, or wheel tag mismatch.

Recovery:

- Decide whether the task truly requires full CUDA execution. Catalog lookup,
  documentation, and tiny CPU shape checks do not.
- For full CUDA reproduction, match torch version, CUDA wheel tag, Python
  version, driver, and hardware before running.
- Record unverified optional CUDA paths explicitly; do not report them as
  passed.

## Output artifacts are written in surprising places

Symptoms: images, plots, frames, or checkpoints appear in the current working
directory or fail because a directory is missing.

Recovery:

- Run adaptations from a scratch workspace.
- Create output directories explicitly.
- Keep generated skill files and review artifacts separate from experiment
  outputs.
