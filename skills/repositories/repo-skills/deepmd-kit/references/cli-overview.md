# DeePMD-kit CLI Overview

Use this reference for quick routing across `dp` commands. Backend-specific details live in the owning sub-skills.

## Backend Flags

| Backend | Aliases | Typical artifacts | Notes |
| --- | --- | --- | --- |
| TensorFlow | `--tf`, `--backend tensorflow` | `.pb` frozen models, TensorFlow checkpoints | Default backend unless `DP_BACKEND` or a flag overrides it. |
| PyTorch | `--pt`, `--backend pytorch` | `.pth` frozen models, `.pt` checkpoints | Common for DPA2/DPA3/DPA4 and pretrained/fine-tune workflows. |
| JAX | `--jax`, `--backend jax` | `.hlo`, `.jax`, `.savedmodel` | SavedModel export also needs TensorFlow runtime for some downstream integrations. |
| Paddle | `--pd`, `--backend paddle` | `.json` + `.pdiparams`, `.pd` checkpoints | Use Paddle install instructions before execution. |
| PyTorch exportable | `--pt-expt`, `--backend pytorch-exportable` | exportable PyTorch artifacts | Use only when the task explicitly asks for exportable/AOT PyTorch behavior. |

## Subcommands

| Command | Owning route | Purpose |
| --- | --- | --- |
| `train` | `sub-skills/training-models/SKILL.md` | Train or fine-tune a model from JSON/YAML input. |
| `freeze` | `sub-skills/training-models/SKILL.md` | Export a trained checkpoint/head to a deployable model artifact. |
| `test` | `sub-skills/inference-model-ops/SKILL.md` | Evaluate a frozen model on labeled DeePMD data. |
| `eval-desc` | `sub-skills/inference-model-ops/SKILL.md` | Save descriptor arrays for a system. |
| `embed` | `sub-skills/inference-model-ops/SKILL.md` | Save embeddings/features, especially for PyTorch workflows. |
| `model-devi` | `sub-skills/inference-model-ops/SKILL.md` | Compare multiple models for uncertainty/deviation. |
| `show` | `sub-skills/inference-model-ops/SKILL.md` | Inspect model metadata such as type map, descriptor, fitting net, branch, or size. |
| `compress` | `sub-skills/inference-model-ops/SKILL.md` | Compress a frozen model. |
| `convert-from` | `sub-skills/inference-model-ops/SKILL.md` | Convert older frozen model versions to newer compatibility. |
| `convert-backend` | `sub-skills/inference-model-ops/SKILL.md` | Convert supported model files between backends. |
| `pretrained download` | `sub-skills/inference-model-ops/SKILL.md` or `sub-skills/training-models/SKILL.md` | Download built-in pretrained models for direct inference or fine-tuning. |
| `change-bias` | `sub-skills/inference-model-ops/SKILL.md` | Adjust model energy bias from data or supplied constants. |
| `neighbor-stat` | `sub-skills/data-config/SKILL.md` and `sub-skills/training-models/SKILL.md` | Estimate/select neighbor counts for descriptors before training. |
| `doc-train-input` | `sub-skills/data-config/SKILL.md` | Generate training input schema/reference output. |
| `gui` | `sub-skills/data-config/SKILL.md` | Launch or support DP-GUI-style training input authoring. |
| `train-nvnmd` | `sub-skills/training-models/SKILL.md` | Specialized NVNMD training path; often environment/account-specific. |
| `transfer` | `sub-skills/training-models/SKILL.md` | Transfer parameters between TensorFlow models. |

## Safe First Checks

Run these before deeper diagnosis:

```bash
python -c "import deepmd; print(deepmd.__version__)"
dp --version
dp -h
dp --pt -h
```

If `dp` fails but Python import works, check whether the environment's console scripts are on `PATH`. If Python import fails, route to `installation-backends`.
