---
name: fengshenbang-lm
description: "Operate the Fengshenbang-LM Fengshen package for pipelines, model
  families, data/training utilities, examples, and conversion planning."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Fengshenbang-LM repo skill

Use this skill when the task involves the Fengshenbang-LM / `fengshen` Python package: Chinese NLP model families, `fengshen-pipeline`, Fengshen pipeline APIs, dataloaders, PyTorch Lightning training helpers, Deepspeed/Megatron planning, model-family examples, Taiyi/Ziya recipes, or checkpoint conversion planning.

## First checks

1. Read [references/installation.md](references/installation.md) before installing or repairing the package. This repo is sensitive to the age of the Transformers, Lightning, Torchmetrics, NumPy, and Setuptools stack.
2. Run the safe install check when an environment is available:

   ```bash
   python scripts/check_fengshen_install.py --check-cli-help
   ```

   This imports package modules and inspects CLI help only; it does not download models or launch training.
3. If imports, CLI help, optional CUDA, model downloads, submodules, or hard-coded example paths fail, read [references/troubleshooting.md](references/troubleshooting.md).
4. Use [references/repo-provenance.md](references/repo-provenance.md) to decide whether this skill matches the current package checkout or should be refreshed.

## Route by task

| User task | Read |
|---|---|
| Use `fengshen-pipeline`, inspect pipeline CLI flags, create tiny classification/NER fixtures, adapt text classification or sequence-tagging data, use UniMC/UniEX/Ubert/TCBert APIs | [sub-skills/pipelines-cli/SKILL.md](sub-skills/pipelines-cli/SKILL.md) |
| Choose or import Fengshen model/config/tokenizer families, understand top-level exports, custom auto/config keys, model compatibility, or model import failures | [sub-skills/model-zoo/SKILL.md](sub-skills/model-zoo/SKILL.md) |
| Prepare/validate data, inspect `UniversalDataModule`, metrics, checkpoints, optimizer/scheduler/Trainer flags, pretraining data, Deepspeed/Megatron/fused-kernel planning | [sub-skills/data-training/SKILL.md](sub-skills/data-training/SKILL.md) |
| Plan CLUE/classification recipes, NLG/NLT examples, Taiyi Stable Diffusion, Ziya inference/fine-tuning/conversion, delta/TF/diffusers/LLaMA conversion utilities | [sub-skills/examples-conversion/SKILL.md](sub-skills/examples-conversion/SKILL.md) |

## Package facts to remember

- Distribution/import package: `fengshen`.
- Version in package metadata: `0.0.1`.
- Console entry point: `fengshen-pipeline = fengshen.cli.fengshen_pipeline:main`.
- CLI pattern: `fengshen-pipeline <pipeline_module_name> predict|train ...`; source CLI supports only `predict` and `train` methods.
- Public top-level exports include Longformer, RoFormer, Megatron-T5, and Ubert classes/pipelines.
- Many examples are real but heavy: they may require model/data downloads, CUDA/Deepspeed, multi-GPU launchers, large memory, checkpoint mutation, or maintainer-local paths. Treat them as planning evidence unless the user explicitly authorizes backend verification and execution.

## Non-goals and safety

- Do not run original repo examples, pretraining scripts, stable-diffusion scripts, Ziya conversion scripts, or fused-kernel tests by default.
- Do not tell the user to open files in the original repository checkout as runtime instructions. Use this skill's bundled references and scripts.
- Do not claim CUDA/Deepspeed/large-model execution is verified from CPU import checks.
- Ask before network downloads, large model/dataset cache use, GPU allocation, multi-node jobs, checkpoint conversion, or overwriting output directories.
- If a task is about editing or refreshing this generated skill after the source repo changes, use the repo-skill refresh workflow rather than relying on stale guidance.
