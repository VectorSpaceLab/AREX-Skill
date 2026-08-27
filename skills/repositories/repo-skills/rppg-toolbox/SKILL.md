---
name: rppg-toolbox
description: "Guide remote photoplethysmography workflows with rPPG-Toolbox,
  including dataset preparation, supervised and unsupervised inference,
  evaluation, visualization, and safe extension."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# rPPG-Toolbox

Use this repo skill when a Researcher needs to work with the rPPG-Toolbox for
camera-based physiological sensing (remote photoplethysmography/rPPG): prepare
supported video-plus-BVP datasets, train or test a neural model, extract BVP
with traditional methods, evaluate heart rate/signal quality, inspect outputs,
or extend a loader/model/method. This skill is an operating guide, not a
replacement for the source package or a claim that data/checkpoints are
available.

## Start here

1. Confirm the user's checkout, Python environment, dataset/cache locations,
   checkpoint provenance, target mode, sampling rate, and whether the operation
   may write caches, checkpoints, plots, or logs.
2. Read [installation and environment guidance](references/installation.md) for
   the Python/PyTorch stack. The repository is not a normal installable Python
   distribution; use an isolated environment and run from the checkout root or
   an explicit import path.
3. Choose a route below. Read only that route's `SKILL.md` first, then its
   linked references and scripts.
4. Validate paths, cache/file-list identity, tensor layout, label type, device,
   and expected output before launching an expensive command.
5. Keep raw data and checkpoints outside the skill tree. Treat preprocessing,
   training, OpenFace, and dataset-scale inference as explicit user-approved
   operations.

## Route map

- **Setup, YAML, and dispatch:** Read
  [setup-and-config](sub-skills/setup-and-config/SKILL.md) when choosing
  `train_and_test`, `only_test`, or `unsupervised_method`, validating a config,
  diagnosing derived paths, or adding a dispatch branch.
- **Datasets and preprocessing:** Read
  [data-preparation](sub-skills/data-preparation/SKILL.md) for raw layouts,
  face crop, transforms, chunking, pseudo labels, custom file lists, splits,
  cache audits, and loader extensions.
- **Supervised neural models:** Read
  [supervised-models](sub-skills/supervised-models/SKILL.md) for exact model
  names, tensor geometry, checkpoints, training/only-test flow, BigSmall, or
  PhysMamba's required CUDA extension.
- **Traditional BVP extraction:** Read
  [unsupervised-methods](sub-skills/unsupervised-methods/SKILL.md) for POS,
  CHROM, ICA, GREEN, LGI, PBV, and OMIT selection and numerical failure
  diagnosis.
- **Metrics and visual outputs:** Read
  [evaluation-and-visualization](sub-skills/evaluation-and-visualization/SKILL.md)
  for HR/RR metrics, SNR/MACC, Bland--Altman, saved prediction pickles,
  preprocessed arrays, and optional OpenFace motion summaries.

## Minimal invocation contract

From a user-owned rPPG-Toolbox checkout, the primary entry point is:

```bash
python main.py --config_file <path-to-user-config.yaml>
```

The source dispatches exact mode strings `train_and_test`, `only_test`, and
`unsupervised_method`. YAML, not the CLI, controls datasets, models, devices,
checkpoints, preprocessing, and output paths. Start from a nearby repository
config, replace all research-specific paths, and use the setup validator before
running the main program. Do not assume a release `.pth` file matches a new
preprocessing identity.

## Cross-route invariants

- The normal cache stores frame-first `*_input*.npy` arrays and paired
  `*_label*.npy` signals; the data layout returned to a model depends on
  `DATA_FORMAT`. Do not silently transpose to hide a model mismatch.
- `DiffNormalized`, `Raw`, and `Standardized` are different label contracts.
  Record the label type and sampling rate with every evaluation or visualization.
- Relative paths resolve from the process working directory. Derived cache,
  file-list, checkpoint, and output identities depend on preprocessing settings;
  use the printed frozen config and a read-only validator rather than guessing.
- A CPU import does not verify PhysMamba. Its `mamba_ssm`/`causal_conv1d` CUDA
  backend must be installed and exercised on a compatible device.
- Missing datasets, checkpoints, OpenFace, or external motion-augmentation
  inputs are explicit limits. Do not download, fabricate, or silently skip
  them and then report a completed experiment.

## Before handoff

Record the route, config identity, dataset/split, cache and file-list paths,
label type, frame rate, device/backend, checkpoint, output location, command,
result, and any skipped or blocked verification. For current-code alignment,
read [repository provenance](references/repo-provenance.md) before using
`refresh-repo-skill`. For cross-cutting failures, read
[troubleshooting](references/troubleshooting.md).

This repo skill was generated as a reusable package/repository operating graph;
it remains self-contained knowledge and does not require the source checkout to
remain available for reading. The actual rPPG run still requires the user's
own data, environment, and permissions.
