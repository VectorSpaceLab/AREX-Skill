# Configuration, artifacts, resume, and migration

## Build order

Fresh training builds configs in this order:

1. load robot config from factory;
2. create simulator config from backend and robot simulation params;
3. run experiment `configure_robot_and_simulator()` if present;
4. build terrain, scene library, motion library, environment, and agent configs from experiment functions;
5. apply scalar CLI overrides;
6. save resolved configs and sidecars.

## Saved artifacts

A run directory normally contains:

- `config.yaml`: CLI args and W&B ID.
- `resolved_configs.pt`: exact pickled Python config objects; primary runtime/resume source.
- `resolved_configs.yaml`: readable sidecar; not source of truth.
- `resolved_configs_inference.pt`: inference-time config objects after evaluation overrides.
- `resolved_configs_inference.yaml`: readable inference sidecar.
- `experiment_config.py`: copied experiment file.
- `last.ckpt`: full checkpoint for resume/warm-start.
- optional score-based or periodic checkpoints.
- optional `inference_last.ckpt`: inference/share artifact for some model families.

## Resume semantics

Same experiment name plus existing run artifacts resumes from saved configs. Training-time CLI overrides are ignored during resume because the saved `.pt` config is exact. If you need config changes, use a new experiment name or regenerate configs intentionally.

## Warm start

New experiment name plus `--checkpoint <path>` loads weights into freshly built configs. Use this when changing the environment/agent config but starting from previous weights.

## Migration

Use `--create-config-only` when code/config class changes require regenerated config objects for old checkpoints. After creating compatible `resolved_configs*.pt`, copy/move them deliberately with the checkpoint only when you understand the compatibility change.

## Inference overrides

Inference loads `resolved_configs_inference.pt` from the checkpoint directory, then applies:

1. inference-specific defaults;
2. experiment `apply_inference_overrides()` if present;
3. inference CLI overrides such as `--motion-file`, `--scenes-file`, `--num-envs`, `--headless`, `--full-eval`, and `--command-source`.

## Pitfalls

- Do not edit YAML sidecars expecting behavior changes.
- Do not use `inference_last.ckpt` for training resume unless a model-specific guide says it is valid.
- Do not copy resolved configs across incompatible code versions without a migration check.
- Do not assume a checkpoint trained in one simulator transfers to another backend.
