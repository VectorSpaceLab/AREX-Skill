# CLI/config troubleshooting

## Invalid command or route

- If `autotrain vlm` fails, this is expected for the inspected checkout. Route VLM requests through app/API/config and the `vision-multimodal` sub-skill.
- If a subcommand help page fails before printing usage, fix the Python environment first; the CLI imports the training parameter classes eagerly.
- If a user mixes CLI task names and app task keys, normalize before giving commands. Examples: `st` maps to sentence-transformers in app params; `image-object-detection` maps to object detection.

## Config parser failures

- Missing or misspelled `task` should be fixed before any training command.
- Backend keys must match known AutoTrain backend keys such as `local`, `local-cli`, `local-ui`, `spaces-*`, `ep-*`, `ngc-*`, or `nvcf-*`.
- Task-specific params should be verified in the owning sub-skill because each trainer has different required columns and optional knobs.
- Use `scripts/validate_config.py --show-parsed` when a YAML file is accepted but the resolved values are surprising.

## Setup pitfalls

- `autotrain setup --update-torch` installs CUDA 12.1 PyTorch wheels. Do not run it in a carefully pinned CPU-only or non-CUDA environment unless the user asked for that replacement.
- `autotrain setup --colab` pins `xformers==0.0.24`; without `--colab`, setup uninstalls `xformers`.
- If setup partially changes the environment, rerun `python -m pip check`, then verify `import torch` and `autotrain --help`.

## Safe recovery sequence

```bash
python -m pip check
python skills/disco/autotrain-advanced/scripts/check_install.py
python skills/disco/autotrain-advanced/scripts/inspect_cli.py --help
python skills/disco/autotrain-advanced/scripts/validate_config.py path/to/config.yml
```

Stop before launching `autotrain --config` if the user only asked for validation or planning.
