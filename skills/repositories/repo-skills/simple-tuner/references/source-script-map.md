# Source script map

This map records how useful SimpleTuner source scripts were distilled into this self-contained skill. Future agents should use the bundled helpers or references here; do not require the original source checkout.

| source artifact | decision | bundled runtime replacement | owner | rationale |
|---|---|---|---|---|
| ControlNet Canny edge dataset script | adapted | `sub-skills/data-and-config/scripts/make_controlnet_canny_edges.py` | `data-and-config` | Original logic was useful and small, but the source script had hardcoded local paths and no CLI. The bundled helper adds argparse, dry-run, thresholds, and overwrite controls. |
| Dataloader/config validation code | distilled/adapted | `sub-skills/data-and-config/scripts/validate_dataloader_config.py` | `data-and-config` | Future agents need a safe standalone structure checker, not a full training import or source checkout. |
| Sharded safetensors merge script | adapted/copied | `sub-skills/model-and-adapter-tooling/scripts/merge_safetensors_shards.py` | `model-and-adapter-tooling` | Original behavior is useful; bundled helper adds dry-run default, JSON reports, output safety, and duplicate-key checks. |
| Model metadata extraction script | wrapped as read-only | `sub-skills/model-and-adapter-tooling/scripts/inspect_model_registry.py` | `model-and-adapter-tooling` | Future agents normally need registry inspection, not source metadata rewrites. |
| Adapter extraction scripts | reference-only | `sub-skills/model-and-adapter-tooling/references/conversion-and-extraction.md` | `model-and-adapter-tooling` | They read/write large checkpoints and may download model weights; require explicit user approval and workflow-specific paths. |
| Format conversion scripts | reference-only | `sub-skills/model-and-adapter-tooling/references/conversion-and-extraction.md` | `model-and-adapter-tooling` | Model file mutation and brittle architecture mappings; distilled into decision/preflight guidance. |
| SDNQ options extraction | reference-only | `sub-skills/model-and-adapter-tooling/references/conversion-and-extraction.md` | `model-and-adapter-tooling` | Maintainer metadata update, not a runtime user helper. |
| Prompt2Effect scripts | reference-only | `sub-skills/model-and-adapter-tooling/references/distillation-and-experimental.md` | `model-and-adapter-tooling` | Multi-step training/checkpoint workflow; not WebUI integrated; requires explicit data/model approval. |
| Masked-loss and lyrics dataset scripts | reference-only | `sub-skills/data-and-config/references/data-preparation.md` | `data-and-config` | Can require model/network/data dependencies; safer to document prerequisites and side-effect gate. |
| Apple Metal flash attention shell script | reference-only | `sub-skills/training-workflows/references/distributed-and-memory.md` | `training-workflows` | Platform build/install side effects; not safe as a default bundled command. |
| Cog deployment script | excluded/reference-only | `sub-skills/webui-and-operations/references/job-queue-cloud-workers.md` | `webui-and-operations` | Deployment and external-service side effects; not part of ordinary operating skill runtime. |
| Webhook documentation generator | reference-only | `sub-skills/repo-development/references/frontend-docs-and-privacy.md` | `repo-development` | Maintainer doc-generation side effect; update docs through repo-development workflow. |
| MiniMax H3 benchmark/verification scripts | reference-only | `sub-skills/model-and-adapter-tooling/references/distillation-and-experimental.md` | `model-and-adapter-tooling` | GPU/distributed benchmark-like runtime; not selected for default verification. |

Root-level bundled helpers are synthetic, safe, and shared:

- `scripts/check_simpletuner_environment.py` probes install/import/CLI and optionally torch backend availability.
- `scripts/list_simpletuner_examples.py` lists installed packaged examples without requiring the source checkout.
