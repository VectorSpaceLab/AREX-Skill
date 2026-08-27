# Source script inventory

This inventory records which repo-owned scripts or runnable examples were distilled into bundled skill helpers or kept as reference-only evidence. It is a source-to-runtime map, not a runtime instruction list.

| Source repo artifact | Workflow / capability | Decision | Bundled target | Rationale | Safety / check |
| --- | --- | --- | --- | --- | --- |
| `examples/datasets/preparing_your_dataset.py` | Alpaca JSON to xTuring instruction dataset conversion | adapt | `sub-skills/data-prep-and-generation/scripts/convert_alpaca_json.py` | Small and reusable after path normalization and input validation. | `--help` plus a tiny JSON roundtrip. |
| `scripts/check_docs_contracts.py` | Docs / CLI / API consistency check | reference-only | none | The original helper depends on source-checkout documentation paths and is not a portable runtime helper. | Keep as evidence only; use `scripts/check_xturing_environment.py` for runtime readiness. |
| `examples/features/dpo/dpo_finetune.py` | DPO alignment recipe | reference-only | `sub-skills/training-and-alignment/references/dpo-workflow.md` | Long-running, GPU-heavy, and model-download dependent. | Reference only; do not bundle a full training runner. |
| `examples/models/qwen3/qwen3_lora_finetune.py` | Qwen3 LoRA fine-tuning recipe | reference-only | `sub-skills/training-and-alignment/references/finetuning-workflows.md` | Useful workflow evidence, but not safe as a default runnable helper. | Reference only; no full training by default. |
| `examples/features/generic/generic_model.py` | GenericModel fine-tuning and inference recipe | reference-only | `sub-skills/models-and-inference/references/inference-workflows.md` | Good workflow evidence, but the bundled skill should use its own distilled workflow notes. | Reference only. |
| `examples/features/generic/generic_lora_model.py` | Generic LoRA fine-tuning recipe | reference-only | `sub-skills/training-and-alignment/references/finetuning-workflows.md` | Useful for target-module guidance, but the source example depends on repo-local paths. | Reference only. |
| `examples/features/evaluation/evaluation.py` | Perplexity evaluation recipe | reference-only | `sub-skills/evaluation/references/evaluation-workflows.md` | Depends on repo-local dataset and model paths; the reusable contract belongs in the evaluation references. | Reference only. |

## Notes

- Runtime helpers that users should run live under `skills/disco/x-turing/scripts/` or the nearest sub-skill `scripts/` directory.
- Source paths are evidence only; runtime instructions always point to bundled files in this skill tree.
