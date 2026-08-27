# Cross-Cutting Troubleshooting

## Use this reference when

Read this before diving into a sub-skill-specific troubleshooting page if the failure is about installation, imports, optional hardware, media codecs, model downloads, or component routing.

## Installation and import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: clearvoice` | The installable package is not installed in the active environment. | Install with `pip install clearvoice` for package use, or install a local checkout's ClearVoice package in editable mode when doing repository development. Then run `scripts/check_clearer_voice_environment.py`. |
| `from clearvoice import ClearVoice` works but version strings differ | The distribution metadata and source `__version__` are not synchronized in this snapshot. | Prefer distribution metadata for packaging/version checks; do not treat source `__version__` alone as proof of staleness. |
| SpeechScore import fails outside its component directory | SpeechScore is source-layout and imports sibling modules such as `scores.*` and `basis`. | Use the bundled SpeechScore helper with `--speechscore-dir` pointing at a user-owned SpeechScore component directory, or run from that component directory after installing runtime requirements. |
| SpeechScore fails with `pkg_resources` while importing `pyworld` | Newer setuptools versions may not provide the deprecated `pkg_resources` module expected by `pyworld`. | Use a setuptools version that still provides `pkg_resources` for that environment, then rerun the import check. |

## Optional backends and media codecs

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| CUDA is unavailable or training says cuDNN must be enabled | CPU-only PyTorch, no visible GPU, driver/container mismatch, or CUDA not selected. | For package inference, CPU may work but can be slow. For training, use a CUDA-capable PyTorch environment and verify with `scripts/check_clearer_voice_environment.py` before launching. |
| Non-WAV audio/video fails to decode or export | FFmpeg or codec support is missing from the environment. | Install FFmpeg through the platform package manager and rerun a small media conversion check before running ClearVoice on mp3/aac/ogg/video inputs. |
| Model creation starts a long download or fails with hub/network errors | ClearVoice downloads checkpoints when absent. | Pre-download required checkpoints from an approved model hub/cache, ensure network/proxy policy is correct, or use dry-run helper modes while planning. Do not start large downloads unless the user requested a real inference run. |

## Safe first checks

- Run `scripts/check_clearer_voice_environment.py` to check ClearVoice import, torch/CUDA visibility, FFmpeg presence, and optional SpeechScore source-layout imports without loading weights.
- For ClearVoice inference, run `sub-skills/clearvoice-inference/scripts/clearvoice_inference_recipe.py --list-models` or a `--dry-run` task/model validation before real inference.
- For SpeechScore, run `sub-skills/speechscore-metrics/scripts/speechscore_metric_recipe.py` without `--run` to validate metric/reference choices.
- For training, run `sub-skills/training-and-data-prep/scripts/inspect_training_config.py --config <config>` before proposing a launcher.

## Stop conditions

Stop and ask for explicit user approval before:

- Starting full model checkpoint downloads.
- Running distributed training or evaluation.
- Generating or overwriting data output trees.
- Reinstalling/downgrading packages in a user-owned environment.
- Changing CUDA/PyTorch variants for a workflow that already has a working environment.
