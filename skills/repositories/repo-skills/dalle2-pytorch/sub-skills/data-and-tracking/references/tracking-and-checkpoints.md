# Tracking, loaders, savers, and checkpoint destinations

DALLE2-pytorch wraps experiment logging, checkpoint loading, and checkpoint saving behind tracker config classes in `dalle2_pytorch.trackers` and `dalle2_pytorch.train_configs`.

## Tracker config shape

A typical training config includes:

```json
"tracker": {
  "data_path": ".tracker-data",
  "overwrite_data_path": false,
  "log": {"log_type": "console"},
  "load": null,
  "save": [{"save_to": "local", "save_latest_to": "latest.pth"}]
}
```

`TrackerConfig.create(...)` builds a `Tracker`, adds one logger, optional loader, and one or more savers, then initializes all components.

## Loggers

### Console

```json
"log": {"log_type": "console"}
```

Safe default. Prints dictionaries and errors; image/file logging is a no-op.

### W&B

```json
"log": {
  "log_type": "wandb",
  "wandb_entity": "ENTITY",
  "wandb_project": "PROJECT",
  "wandb_run_name": "optional-name",
  "wandb_run_id": "optional-resume-id",
  "resume": false,
  "auto_resume": false,
  "verbose": true
}
```

Requirements and caveats:

- Python package `wandb` and network access.
- `wandb_entity` and `wandb_project` are required.
- `resume: true` requires `wandb_run_id`.
- The logger sets `WANDB_SILENT=true`.
- Do not store secrets or API keys in public config templates.

## Loaders

### Local loader

```json
"load": {"load_from": "local", "file_path": "path/to/checkpoint.pth"}
```

`LocalLoader.init` raises `FileNotFoundError` unless the file exists or `only_auto_resume` is true.

### URL loader

```json
"load": {"load_from": "url", "url": "https://.../checkpoint.pth"}
```

Downloads to tracker data path before `torch.load`. Treat as a network workflow.

### W&B loader

```json
"load": {
  "load_from": "wandb",
  "wandb_run_path": "entity/project/run_id",
  "wandb_file_path": "model/latest.pth"
}
```

Requires `wandb`, network, and permissions for the run.

## Savers

`save` may be one object or a list of saver configs.

Common fields:

- `save_to`: `local`, `wandb`, or `huggingface`.
- `save_latest_to`, `save_best_to`, `save_meta_to`: destination paths or false/null.
- `save_type`: `checkpoint` or `model`.

At least one of latest, best, or metadata saving must be enabled.

### Local saver

```json
"save": [{"save_to": "local", "save_latest_to": "latest.pth", "save_best_to": "best.pth"}]
```

Safest default. The saver creates parent directories as needed.

### W&B saver

```json
"save": [{"save_to": "wandb", "save_latest_to": "latest.pth"}]
```

Requires an active W&B run or `wandb_run_path`. The saver copies files into the tracker data path then calls W&B save.

### HuggingFace saver

```json
"save": [{
  "save_to": "huggingface",
  "huggingface_repo": "user/repo",
  "token_path": "optional-token-file",
  "save_latest_to": "model/latest.pth",
  "save_type": "model"
}]
```

Requires `huggingface_hub`, authentication, network, and write permission. If CLI login is unavailable, `token_path` must point to a token file.

## Checkpoint format distinctions

- Trainer checkpoints from `DecoderTrainer.save` and `DiffusionPriorTrainer.save` include optimizer, scheduler, EMA, scaler, step/version, and model state.
- The `dream` CLI expects a combined DALLE2 checkpoint with `version`, `init_params.prior`, `init_params.decoder`, and `model_params` keys.
- Do not try to load a trainer checkpoint directly with `dream` unless you have converted it to the combined format.

## Auto-resume notes

- Loggers can provide resume metadata through `get_resume_data`.
- Loaders can be configured with `only_auto_resume`.
- Distributed runs should ensure every rank sees consistent tracker state; source decoder launcher waits before tracker creation to reduce auto-resume races.

## Privacy and publication

- Keep W&B entities, run IDs, HuggingFace repos, token paths, S3 buckets, and local checkpoint paths out of reusable public templates unless the user intentionally supplies publishable placeholders.
- In answers, ask users to provide credentials or choose local/console mode; do not infer credentials from environment variables.
