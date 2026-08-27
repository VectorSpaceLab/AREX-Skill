---
name: training-config
description: "Integrate DeepSpeed training into PyTorch, author and validate
  config JSON/HJSON, plan launcher resources, choose ZeRO/offload settings, and
  handle checkpoint save/load/export safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DeepSpeed Training Config

Use this sub-skill when a future agent needs to wire DeepSpeed into a PyTorch training loop, create or audit `ds_config.json`, build `deepspeed` launcher commands, select ZeRO stages/offload, or plan training checkpoint save/load/export. This sub-skill covers training runtime setup only; route inference-only kernel injection to `inference-injection`, pipeline/MoE/sequence parallel details to `parallelism-moe`, and build diagnostics to `ops-tooling`.

## Fast Path

1. Integrate the model with `deepspeed.initialize(...)`; call `deepspeed.init_distributed()` only when the script needs a distributed process group before `initialize`.
2. Author config through `references/configuration.md`, then run `scripts/validate_ds_config.py --world-size <ranks> ds_config.json` before launching.
3. Build resource filters and `--no_ssh` commands through `references/launcher-and-checkpointing.md`; preview filters with `scripts/launcher_resource_preview.py`.
4. Choose ZeRO settings with `references/configuration.md`, keeping deprecated aliases out of new configs.
5. Plan checkpoint calls so all ranks participate; for ZeRO-3 exports, enable `stage3_gather_16bit_weights_on_model_save` or use the generated `zero_to_fp32.py`/utility path after checkpointing.

## Bundled References

- `references/api-reference.md`: `deepspeed.initialize`, `init_distributed`, engine training calls, `DeepSpeedConfig`, and `DeepSpeedZeroConfig` field facts.
- `references/configuration.md`: batch-size contract, JSON/HJSON authoring, precision, optimizer/scheduler, ZeRO/offload choices, and safe validation workflow.
- `references/launcher-and-checkpointing.md`: launcher hostfile/include/exclude/no-SSH syntax plus checkpoint save/load/export guardrails.
- `references/troubleshooting.md`: common failures and fixes for config parsing, launcher filters, checkpoint hangs, ZeRO-3 export, and CUDA op probing.

## Bundled Scripts

- `scripts/validate_ds_config.py`: Parses JSON or HJSON when `hjson` is installed, detects duplicate JSON keys, checks batch-size consistency, and warns about selected ZeRO pitfalls without importing or launching DeepSpeed.
- `scripts/launcher_resource_preview.py`: Parses hostfile text plus `--include`/`--exclude` style filters and reports the selected resources or conflicts without launching training.

## Native Candidates

Safe native candidates to consult during verification are the config parser/dict tests and launcher parser tests. Broad GPU/distributed checkpoint matrices should be skipped by default unless the verifier has explicit safe hardware and time approval.
