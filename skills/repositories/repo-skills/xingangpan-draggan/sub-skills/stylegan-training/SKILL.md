---
name: stylegan-training
description: "Guides StyleGAN-Human SHHQ training with the bundled
  StyleGAN2/StyleGAN3 command builders, dataset layout checks, GPU planning, dry
  runs, resumes, and training troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# StyleGAN-Human Training

Use this route when the user wants to train or resume StyleGAN2-ADA or StyleGAN3 on SHHQ, adapt the paper-scale eight-GPU recipes, validate dataset/output paths, or diagnose training command failures.

## Safety and scope

Training is expensive and asset-gated. Do not launch a long run from a generic request. First confirm the user has lawful access to SHHQ, a prepared dataset directory or zip, enough GPU memory/storage, and a desired run budget.

The bundled builder only prints a command:

```bash
python sub-skills/stylegan-training/scripts/build_training_command.py \
  --repo-root /path/to/DragGAN --version sg2 \
  --data data/SHHQ-1.0 --outdir training_results/sg2 \
  --gpus 1 --batch 4 --kimg 10 --dry-run-flag
```

The `training_scripts/sg2` and `training_scripts/sg3` files in StyleGAN-Human are modified training entry points and network files, not always complete standalone training roots. If the builder warns about missing support modules such as `metrics/`, `training_loop.py`, `torch_utils/`, or `dnnlib/`, apply the StyleGAN-Human modifications to a complete StyleGAN2-ADA or StyleGAN3 training tree and pass `--training-root <prepared-root>` before executing.

Use [references/training-workflows.md](references/training-workflows.md) for SG2/SG3 recipes, [references/dataset-and-config.md](references/dataset-and-config.md) for SHHQ layout and legal/config constraints, and [references/troubleshooting.md](references/troubleshooting.md) before retrying a failed run.

## Workflow decisions

- **SG2-ADA:** `--cfg shhq`, `--data`, `--gpus`, `--aug`, `--mirror`, `--snap`, and `--square False`; `--batch`, `--gamma`, and `--kimg` can override the base config.
- **SG3:** `--cfg stylegan3-r` (or `stylegan3-t`), `--data`, `--gpus`, `--batch`, `--gamma`, `--mirror`, `--aug`, `--square False`, and `--snap` are required/planned controls.
- **Debug run:** reduce GPUs, batch, and `kimg`; keep a separate output directory; use `--dry-run` first.
- **Paper-scale reproduction:** the README examples use eight GPUs and long schedules. Match the paper recipe only when the hardware, data, and budget are explicitly available.
- **Resume:** pass a compatible network pickle with `--resume`; record the source run, config, data version, and changed options.

## Related routes

- Batch inference and generation: [../stylegan-generation/SKILL.md](../stylegan-generation/SKILL.md).
- Alignment, PTI, and human attribute editing: [../stylegan-human-manipulation/SKILL.md](../stylegan-human-manipulation/SKILL.md).
- DragGAN interactive editing: [../draggan-ui/SKILL.md](../draggan-ui/SKILL.md).

## Bundled files

- [scripts/build_training_command.py](scripts/build_training_command.py) prints SG2/SG3 commands and can validate the data path without launching training.
- [references/training-workflows.md](references/training-workflows.md) explains command construction, dry runs, snapshots, and resumes.
- [references/dataset-and-config.md](references/dataset-and-config.md) explains SHHQ access, directory/zip expectations, rectangle geometry, and output conventions.
- [references/troubleshooting.md](references/troubleshooting.md) covers CUDA, OOM, dataset, resume, metrics, and multi-GPU problems.
