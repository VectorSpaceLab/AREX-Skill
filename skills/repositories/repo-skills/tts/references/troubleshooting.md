# Cross-Cutting Troubleshooting

## Purpose

Read this first for install/import/version/backend issues that affect more than one Coqui TTS workflow. Then read the nearest sub-skill troubleshooting page for workflow-specific symptoms.

## Fast diagnosis table

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'TTS'` | Package not installed into the current Python, or wrong interpreter selected | Re-run the root smoke checker and confirm `python -c "import TTS"` from the target environment. |
| `Python 3.12+` or `3.13+` warnings | Unsupported interpreter for this snapshot | Use Python `3.9`, `3.10`, or `3.11`. |
| `No broken requirements found` is missing / `pip check` fails | Dependency mismatch or partial install | Fix the environment before relying on any sub-skill. |
| `soundfile` / `libsndfile` / `librosa` / `torchaudio` import errors | Missing audio system dependency or incompatible wheel | Install the package's audio dependencies in a supported Python environment and rerun the smoke checker. |
| `espeak` / `espeak-ng` missing | Optional phonemizer backend unavailable | Use character-mode workflows or install an espeak-compatible backend before phoneme-specific tasks. |
| `torch.cuda.is_available() == False` on a GPU host | CPU-only torch wheel, driver mismatch, or no GPU passthrough | Use CPU-only verification or reinstall a CUDA-capable torch build that matches the host. |
| Model download or TOS prompts appear unexpectedly | A released-model workflow was invoked without explicit approval | Re-run with the sub-skill's dry-run / no-download path or add the explicit acknowledgement flag. |
| Dataset/config load errors mentioning `formatter`, `meta_file_train`, `audio`, or `generator_model` | Wrong config family or missing required fields | Route to the training/config or vocoder sub-skill and validate the file with the bundled config helpers. |
| Output wav/statistics files already exist | Helper is refusing to overwrite by default | Choose a new path or pass the sub-skill's explicit overwrite flag only after review. |

## Cross-cutting recovery order

1. Run [scripts/check_tts_environment.py](../scripts/check_tts_environment.py) to confirm the package, imports, CLI help, and optional CUDA smoke.
2. Confirm the active interpreter is Python `3.9-3.11` and that `pip check` passes.
3. Verify the relevant input files or dataset directories exist.
4. Re-check whether the task is really inference, CLI, training/config, vocoder/audio, or voice conversion; route to the correct sub-skill if needed.
5. Only then retry the workflow-specific helper or command.

## Common backend and cache issues

- **CUDA available but not used**: some workflows default to CPU; request the GPU path explicitly in the sub-skill only when the task needs it.
- **Model cache is stale or missing**: model-loading workflows may create cache and download files. If the user did not approve that, use the dry-run or metadata-only path instead.
- **Network-unavailable environment**: released-model loading and some test fixtures cannot complete. Use bundled no-download helpers where available.
- **Path confusion**: future agents should always point to installed-package or skill-bundled files, not the original repository checkout.

## Where to go next

- Inference/model-zoo errors: [../sub-skills/inference-and-model-zoo/references/troubleshooting.md](../sub-skills/inference-and-model-zoo/references/troubleshooting.md)
- CLI/server errors: [../sub-skills/server-and-cli/references/troubleshooting.md](../sub-skills/server-and-cli/references/troubleshooting.md)
- Training/config/data errors: [../sub-skills/training-config-data/references/troubleshooting.md](../sub-skills/training-config-data/references/troubleshooting.md)
- Vocoder/audio errors: [../sub-skills/vocoder-and-audio-tools/references/troubleshooting.md](../sub-skills/vocoder-and-audio-tools/references/troubleshooting.md)
- Voice-conversion errors: [../sub-skills/voice-conversion/references/troubleshooting.md](../sub-skills/voice-conversion/references/troubleshooting.md)
