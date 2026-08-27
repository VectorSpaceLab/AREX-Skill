# ESPnet3 Configuration

ESPnet3 uses Hydra/OmegaConf configuration roles:

- `training_config`: dataset creation, tokenizer training, statistics, and model training.
- `inference_config`: inference stage setup.
- `metrics_config`: measurement/evaluation stage setup.
- `publication_config`: model packaging and upload metadata.
- `demo_config`: demo packaging and upload configuration.

The runner loads and merges defaults, applies shared experiment context, validates requested stages, instantiates the selected `System`, then calls stage methods.

## Practical guidance

- Keep config roles explicit; do not pass a training config as an inference config just to satisfy the parser.
- Preserve requested stage order unless the template or user requires `all`.
- Treat publication, upload, Hugging Face, and demo stages as network/credential-sensitive.
- Use dry-run/stage inspection for planning, then run only safe subsets unless the user approves expensive stages.
- Route ESPnet2 shell recipe requests back to the recipes/data and ESPnet2 training sub-skills; ESPnet3 stage runners are a different interface.
