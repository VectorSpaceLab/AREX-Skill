# Troubleshooting

## Purpose

Read this when the repo-wide environment, import, or data layout does not match
what the example scripts expect.

## Common cross-cutting issues

### No installable top-level package

**Symptoms**
- There is no `pip install -e .` target.
- The example scripts expect you to work inside the framework directories.

**Cause**
- This repository is a code-example bundle, not a packaged library.

**Recovery**
- Install the dependencies listed in the selected framework's `requirements.txt`.
- Use the framework sub-skill for the exact command and working directory.

### Missing or wrong experiment config

**Symptoms**
- Training or evaluation stops with a missing `params.json` assertion.

**Cause**
- The example command points at an experiment directory that does not contain a
  starter config.

**Recovery**
- Copy or reuse one of the starter experiment directories under
  `pytorch/*/experiments/` or `tensorflow/*/experiments/`.
- Confirm the selected sub-skill's configuration notes before retrying.

### Shared helper imports fail

**Symptoms**
- `ImportError` for `torch`, `torchvision`, `tensorflow`, `PIL`, `tabulate`,
  or `tqdm`.

**Cause**
- The environment is missing the shared runtime helpers or has incompatible
  framework pins.

**Recovery**
- Run `scripts/check_env.py` first.
- Reinstall the framework requirements into a fresh isolated environment when
  the shared check shows a mismatch.

### GPU is visible but a workflow should still run on CPU

**Symptoms**
- The host has CUDA hardware, but you want the portable path.

**Cause**
- The example scripts auto-use CUDA when the framework reports it.

**Recovery**
- Keep the environment CPU-only for the workflow you want to validate, or use a
  framework/wheel combination that does not expose CUDA.
- Do not assume the GPU path is required for this repository; it is optional for
  the generated skill.

## Framework-specific issues

- TensorFlow 1.15 import failures and legacy CUDA library notes belong in
  `sub-skills/tensorflow-examples/references/troubleshooting.md`.
- SIGNS and NER data-layout details belong in the framework sub-skills.
