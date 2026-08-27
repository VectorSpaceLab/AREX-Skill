---
name: sa-prot
description: "Use SaProt for structure-aware protein language modeling, AA+3Di
  sequence conversion, model inference, LMDB configs, training, and
  mutation-effect evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SaProt Repo Skill

Use this skill when a task involves SaProt, structure-aware protein language modeling, AA+3Di tokens, Foldseek 3Di sequences, SaProt checkpoints, mutation-effect scoring, inverse folding, SaProt LMDB datasets, YAML task configs, fine-tuning, pretraining, ProteinGym, or ClinVar evaluation.

SaProt expects structure-aware sequences where each residue is represented as an amino acid plus a Foldseek 3Di token, such as `M#EvVpQpL#VyQdYaKv`. The 35M and 650M SaProt checkpoints work best with SA-token input for frozen embeddings; the 1.3B variants are documented as stronger for AA-only workflows.

## Quick Start

1. Read `references/setup-and-dependencies.md` to decide whether the task needs only static checks, Foldseek conversion, model inference, or the full training stack.
2. Run the shared checker when the user provides local assets:
   `python scripts/check_sa_prot_environment.py --model-dir <local-model-dir> --foldseek <foldseek>`
3. Route to the focused sub-skill for the main task.
4. Keep heavyweight steps explicit: model downloads, full benchmark datasets, GPU training, and Foldseek installation are user-provided prerequisites, not bundled by this skill.

## Route Map

- `sub-skills/structure-sequences/SKILL.md`: convert PDB/mmCIF structures to amino-acid, Foldseek 3Di, or combined AA+3Di sequences; diagnose Foldseek and pLDDT masking.
- `sub-skills/model-inference/SKILL.md`: load local SaProt model assets, tokenize combined sequences, extract embeddings, score mutations, predict substitution effects/probabilities, or run inverse folding.
- `sub-skills/datasets-configs/SKILL.md`: build/validate SaProt LMDB splits, inspect JSON row schemas, edit task YAMLs, and validate config paths without importing heavy ML frameworks.
- `sub-skills/training-evaluation/SKILL.md`: adapt pretraining, fine-tuning, zero-shot mutation benchmark, ClinVar AUC, Lightning trainer, WandB, checkpoint, and GPU settings safely.

## Common Task Routing

| User asks for | Read |
| --- | --- |
| Convert a structure to SaProt input | `sub-skills/structure-sequences/SKILL.md` |
| Understand `M#EvVp` tokenization or pLDDT masking | `sub-skills/structure-sequences/references/sequence-formats.md` |
| Load `SaProt_650M_AF2` or validate local weights | `sub-skills/model-inference/SKILL.md` and `sub-skills/model-inference/references/model-assets.md` |
| Score `V3A` or `V3A:Q4M` mutations | `sub-skills/model-inference/SKILL.md` |
| Create LMDB data from JSONL rows | `sub-skills/datasets-configs/SKILL.md` |
| Adapt a task config from GPU to CPU/one-GPU smoke | `sub-skills/datasets-configs/SKILL.md`, then `sub-skills/training-evaluation/SKILL.md` |
| Run or dry-run fine-tuning/evaluation launchers | `sub-skills/training-evaluation/SKILL.md` |
| Merge ClinVar prediction logs and labels into AUC | `sub-skills/training-evaluation/SKILL.md` |

## Minimal Environment Checks

Use these checks before writing code that imports SaProt modules:

```bash
python scripts/check_sa_prot_environment.py --check-python-imports
python scripts/check_sa_prot_environment.py --model-dir <local-model-dir>
python scripts/check_sa_prot_environment.py --foldseek <foldseek>
```

For model-specific asset validation, use `sub-skills/model-inference/scripts/check_model_assets.py`. For config validation, use `sub-skills/datasets-configs/scripts/validate_config.py` or `sub-skills/training-evaluation/scripts/saprot_config_check.py` depending on whether the task is data/config preparation or launch-risk review.

## Safety Rules

- Do not launch pretraining, downstream fine-tuning, ProteinGym-wide evaluation, or ClinVar-wide evaluation unless the user explicitly asks for an expensive run.
- Do not assume model weights, Foldseek, or LMDB datasets are bundled; validate user-provided local paths.
- Do not paste WandB API keys into shared configs. Prefer private environment variables or disable logging for dry-runs.
- Do not hard-code CUDA. Choose CPU-safe diagnostics first, then move to GPU only after checking the installed PyTorch/CUDA stack and model size.
- Treat example paths such as `LMDB/`, `weights/PLMs/`, and `bin/foldseek` as conventions to adapt inside the user’s active project.

## References

- `references/setup-and-dependencies.md`: install modes, optional dependencies, model/data/Foldseek prerequisites, and quick check commands.
- `references/troubleshooting.md`: cross-cutting import, path, asset, GPU, logging, and stale-skill issues.
- `references/repo-provenance.md`: source snapshot used to decide when this skill may need refresh.
- `references/repo-routing-metadata.json`: structured routing metadata used by `repo-skills-router` during import.
