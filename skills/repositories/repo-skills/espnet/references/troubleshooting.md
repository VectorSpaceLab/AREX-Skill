# ESPnet Cross-cutting Troubleshooting

## Symptom router

| Symptom | Likely owner | First action |
| --- | --- | --- |
| `ModuleNotFoundError` during import | installation | Run the environment checker with the focused group for the workflow and identify the missing optional extra. |
| `Failed to import Flash Attention` | installation/training | Treat as optional fallback unless the selected config requires FlashAttention; do not install it blindly. |
| Missing `sox`, `ffmpeg`, `flac`, `sph2pipe`, or SentencePiece executables | installation/data | Check host tools; recipes/audio/tokenization may need them, but basic package imports do not. |
| `wav.scp`/`segments`/speaker mismatch | recipes/data | Validate the split with `validate_kaldi_data_dir.py` before launching a recipe. |
| Script fails because `utils/` or `path.sh` is missing | recipes/data | Confirm the command is being run from an ESPnet recipe task directory, not a dataset parent or `local/` subdir. |
| `--batch-size` or another hyphenated flag is rejected | training | ESPnet2 Python options generally use underscores, e.g. `--batch_size`. |
| `--print_config` changes after selecting an encoder/optimizer | training | This is expected: nested defaults are dynamic for the selected class choice. |
| CPU dry-run passes but training fails on real data | training | Check data files, dump paths, real iterator settings, memory, optional kernels, and backend runtime separately. |
| CUDA is visible but recipe OOMs | training | Reduce batch size/bins, beam/nbest, or model size; a tiny CUDA tensor allocation is not full training proof. |
| `from_pretrained` fails with model tag, network, or cache errors | inference | Separate model-zoo download/cache handling from local config/checkpoint inference. |
| Local inference fails with config/checkpoint mismatch | inference | Validate file presence, then confirm task family and that config/model come from the same training run. |
| ESPnet3 reports missing config for a stage | ESPnet3 | Use the stage inspector to map requested stages to required config flags. |
| Full CI is too slow or optional imports fail | development | Select focused tests and install only the selected extra/test dependencies. |

## Triage rules

1. Identify whether the user is using ESPnet as a package, an ESPnet2 recipe checkout, an ESPnet3 system checkout, or a maintainer source tree.
2. Keep package, recipe, training, inference, ESPnet3, and contribution workflows separate until the concrete failure needs a cross-link.
3. Do not install `.[all]` just because one optional import failed.
4. Do not launch full `run.sh`, model downloads, demos, uploads, broad CI, or long training without approval.
5. Do not claim GPU/distributed support from CPU imports, parser checks, or synthetic usability cases.
6. Keep local machine paths, private environment names, pip locations, and cache paths out of public answers.
