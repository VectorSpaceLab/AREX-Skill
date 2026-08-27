# ESPnet3 Troubleshooting

## Stage/config errors

- **`Config not provided for stage(s)`**: map each requested stage to required config flags with the stage inspector.
- **Unknown stage**: use `all` or a stage from the template list; do not invent stage names from ESPnet2 shell recipes.
- **Hydra merge failure**: check YAML syntax, defaults, package context, unresolved interpolation, and role-specific config content.
- **Wrong config role**: a training config is not a substitute for `--inference_config` or `--metrics_config`.

## Execution boundaries

- `--dry_run` and the bundled stage inspector are planning tools; they do not prove datasets, model files, metrics, or publication credentials.
- `pack_model`, `upload_model`, `pack_demo`, and `upload_demo` can create artifacts, require credentials, or start publication workflows. Ask before running them.
- ESPnet3 System/Hydra workflows are separate from ESPnet2 `run.sh`; route shell recipe errors to the recipes/data sub-skill.

## Logging and ranks

ESPnet3 stage utilities can write per-stage or per-rank logs. For distributed training failures, distinguish logging/rank naming from actual backend/NCCL failures.
