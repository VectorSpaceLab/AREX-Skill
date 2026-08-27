---
name: training
description: "Routes ICEdit LoRA and MoE LoRA training, dataset preparation,
  config interpretation, launch-command construction, wandb usage,
  checkpointing, and expensive-run caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# training

Use this sub-skill when you need to validate, launch, or troubleshoot ICEdit training runs for the normal LoRA or MoE LoRA paths.

## Use this route for

- Understanding the two shipped configs and how they map to `src.train.train` vs `src.train.train_moe`.
- Preparing or validating the training parquet dataset files.
- Interpreting `flux_path`, `dtype`, `model`, `train.dataset`, `lora_config`, `optimizer`, `wandb`, and checkpoint fields.
- Building the `XFL_CONFIG` / `PYTHONPATH` / `CUDA_VISIBLE_DEVICES` / `accelerate launch` command without starting an expensive run.
- Diagnosing missing parquet files, MagicBrush / OmniEdit access failures, wandb, CUDA, and import problems.
- Checking where LoRA weights and sample images are written.

## Do not use this route for

- Demo launch or browser workflow questions. Use the demo route instead.
- Inference CLI usage. Use the inference route instead.
- Bulk downloads or full training unless the caller explicitly wants a real GPU job.

## Read first

- `references/workflows.md`
- `references/configuration.md`
- `references/dataset-preparation.md`
- `references/troubleshooting.md`

## Skill-owned scripts

- `scripts/launch_train.py` — dry-run by default; resolves the checkout's `train/train/config/`, prints the exact launcher, and can opt in to execution with `--execute`.

The helper does not bundle the training source. A real run requires an ICEdit checkout containing `train/src/train/` and `train/train/config/`; MoE additionally requires the checkout's vendored `icedit/` package. Use `--repo-root <ICEdit checkout>` when automatic discovery is not possible. Missing parquet, local checkpoint, or LoRA paths are warnings in dry-run and block `--execute`.

## Typical workflow

1. Decide whether you need normal LoRA or MoE LoRA.
2. Resolve the config and confirm the dataset path exists or is intentionally remote.
3. Use the bundled helper in dry-run mode to inspect the exact `accelerate` command and env vars.
4. Only execute a real run when the config, dataset, CUDA mapping, and wandb choice are all deliberate.
5. Inspect `runs/<timestamp>/config.yaml`, `runs/<timestamp>/ckpt/<step>/`, and sample images after the run.

## Expensive or networked actions

- The repo's bulk parquet download helper downloads many shards from Hugging Face and should be treated as a manual data-provisioning step.
- `load_dataset('osunlp/MagicBrush')` can hit the network and may fail offline.
- A full `accelerate launch` consumes GPU time and should not be started from a pure question-answering request.

## Cross-links

- If the user actually wants to edit or generate images after training, switch to the inference route.
- If they want the browser demo, switch to the demo route.
