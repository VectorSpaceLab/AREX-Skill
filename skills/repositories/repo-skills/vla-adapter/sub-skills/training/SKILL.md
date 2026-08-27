---
name: training
description: "Builds VLA-Adapter fine-tuning plans and safe torchrun commands
  for LIBERO, CALVIN-style, and ALOHA data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training (external-checkout adapter)

This sub-skill renders a training plan for an external native checkout. The
generated skill contains only documentation and a command builder; it does not
contain `vla-scripts/finetune.py`, does not run `torchrun`, and is not a
self-contained training environment.

Before any native command, use an absolute checkout root:

```bash
export VLA_ADAPTER_REPO_ROOT=/abs/path/to/VLA-Adapter
cd "$VLA_ADAPTER_REPO_ROOT"
python -m pip install -e "$VLA_ADAPTER_REPO_ROOT"
```

The native source entrypoint is `vla-scripts/finetune.py`; the bundled
`build_finetune_command.py` only prints a command beginning with
`cd <absolute-repo-root> &&` and never launches it. External prerequisites are
the native checkout, its base dependencies, CUDA-capable PyTorch and suitable
GPU memory, a compatible pretrained Prismatic VLM/config, the selected
LIBERO/CALVIN/ALOHA dataset and TFDS/dlimp or robot stack, and W&B credentials
or offline logging configuration as applicable.

## Read and run

- Read [references/training-workflows.md](references/training-workflows.md) for
  end-to-end fine-tuning flows, LIBERO/CALVIN/ALOHA recipes, VRAM profiles,
  checkpoint output behavior, resume, and LoRA merge notes.
- Read [references/configuration.md](references/configuration.md) for important
  `FinetuneConfig` fields and option interactions.
- Read [references/troubleshooting.md](references/troubleshooting.md) for CUDA
  OOM, FlashAttention, W&B, LoRA merge, dataset, and resume failures.
- Run `python "$VLA_ADAPTER_SKILL_ROOT/sub-skills/training/scripts/build_finetune_command.py" --repo-root "$VLA_ADAPTER_REPO_ROOT" --help` to inspect the renderer. It is not the training API and never launches `torchrun`.

## Workflow

1. Route setup and data-root questions to
   [setup-and-data](../setup-and-data/SKILL.md) first.
2. Pick the benchmark family and GPU profile.
3. Decide whether the run should use Pro (recommended), LoRA, frozen/full-save
   mode, proprioception, image augmentation, and checkpoint merging during
   training.
4. Generate a command with the bundled builder using an explicit
   `--repo-root "$VLA_ADAPTER_REPO_ROOT"`; inspect paths, W&B settings, GPU
   count, output directory, and storage impact.
5. Launch native `vla-scripts/finetune.py` only from the emitted checkout-root
   guard after confirming data, checkpoint/VLM paths, CUDA memory, and runtime.
6. After training, route checkpoint validation or offline LoRA merge to
   [package-apis](../package-apis/SKILL.md), and benchmark rollouts to
   [evaluation](../evaluation/SKILL.md).

## Defaults to remember

- Pro version is recommended for most new runs.
- LIBERO/CALVIN recipes use 2 images, proprioception, LoRA rank 64, and
  8-action chunks.
- ALOHA recipes use 3 images, 14D proprio/actions, 25-action chunks, and a
  4-GPU launcher by default.
- W&B can run offline or be replaced with local logs for machines without
  credentials.

## Do not

- Do not launch full training from this skill without confirming dataset size,
  checkpoint paths, output storage, GPU memory, and runtime budget.
- Do not treat CPU import success as proof that training can run.
- Do not patch ALOHA local-model source files without an explicit restore plan.
