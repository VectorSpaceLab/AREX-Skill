---
name: mattergen
description: "Guide MatterGen inorganic-crystal generation, structure
  evaluation, dataset preparation, Hydra training, and property fine-tuning with
  CUDA-aware validation and safe artifact handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MatterGen

MatterGen is a generative model for inorganic materials design. Use this root
route to choose the smallest workflow-specific guide before running commands.
The generated skill is self-contained: it describes package contracts and
bundles safe preflight helpers, but it does not download checkpoints, datasets,
MatterSim potentials, or start expensive jobs implicitly.

## First route the request

- **Generate crystal structures** — read
  [generation](sub-skills/generation/SKILL.md). This covers named or local
  checkpoints, unconditional/property/multi-property sampling, CSP target
  compositions, guidance, sampling overrides, and output files.
- **Score or relax structures** — read
  [evaluation](sub-skills/evaluation/SKILL.md). This covers MatterSim relaxation,
  precomputed-energy evaluation, matching, compatible references, correction
  schemes, and metrics.
- **Prepare or validate data** — read
  [data-preparation](sub-skills/data-preparation/SKILL.md). This covers MP-20 and
  Alex-MP-20 layout, CSV schema, cache splits, custom properties, and storage
  preflight.
- **Train or fine-tune** — read
  [training-finetuning](sub-skills/training-finetuning/SKILL.md). This covers
  Hydra base/CSP training, adapters, multi-property wiring, custom embeddings,
  resource controls, and no-launch validation.

For a request that spans routes, prepare data first, train/fine-tune second,
generate third, and evaluate last. Keep each stage's inputs, resolved config,
checkpoint identity, data/reference version, device, and output directory in an
external experiment record.

## Install and smoke-check

MatterGen requires Python 3.10+; the repository's documented Linux path uses a
CUDA-capable PyTorch stack. Install the package using its supported distribution
or editable source checkout, then run the bundled environment check:

```bash
python -m pip install -e <mattergen-source>
python <mattergen-skill-root>/scripts/check_environment.py
```

The source distribution pins a Linux CUDA family around PyTorch 2.2.1 + cu118
and matching PyG extensions. Respect the package's platform-specific install
instructions rather than mixing CPU/CUDA/ROCm wheels. Apple Silicon is
experimental and requires `PYTORCH_ENABLE_MPS_FALLBACK=1` for documented MPS
runs. Read [installation and assets](references/installation-and-assets.md)
when deciding package variants, checkpoints, Git LFS, Hugging Face access, or
large data acquisition.

The helper checks package metadata/imports and reports CUDA/MPS availability;
it does not install packages, contact external services, or launch a model.
Read [API and CLI overview](references/api-and-cli-overview.md) for the five
console entry points and the verified public Python objects.

## Operational guardrails

1. Treat checkpoint, dataset, reference, and potential files as explicit
   inputs. An LFS pointer is not a hydrated model or archive.
2. Preflight arguments, paths, schemas, and backend availability before any
   large job. Use the nearest bundled helper; dry-run is the default where
   offered.
3. Keep generation/evaluation on a visible CUDA device when the workflow needs
   the GPU. CPU checks validate imports and lightweight behavior, not full
   generation throughput or MatterSim relaxation.
4. Use a new output directory for retries. Preserve resolved configs and
   partial artifacts rather than silently overwriting them.
5. Do not compare MP2020 and TRI2024 evaluation results as if they used the
   same hull/reference convention; do not treat MatterSim predictions as DFT.
6. Before publication or scientific claims, record data/license provenance,
   conditioning/checkpoint identity, random seeds, sampling settings, device,
   and whether metrics came from MatterSim or DFT.

For cross-cutting install, import, backend, asset, and artifact failures, read
[troubleshooting](references/troubleshooting.md). For source-version checks or
refresh decisions, read [repository provenance](references/repo-provenance.md).
