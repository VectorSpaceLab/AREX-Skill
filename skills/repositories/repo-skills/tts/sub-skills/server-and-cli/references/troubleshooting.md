# Server And CLI Troubleshooting

Use this for `tts` and `tts-server` command failures after package installation is basically working. For import, Python-version, PyTorch/audio-library, or cache/network issues that are not CLI-specific, also use [../../../references/troubleshooting.md](../../../references/troubleshooting.md).

## `tts` parser and command-building failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `tts` prints the long help text and exits without audio. | No action flag was provided. A command with only `--model_name`, `--vocoder_name`, `--device`, or path flags is not enough. | Add `--text ... --out_path ...` for synthesis, `--list_models`, `--model_info_by_name ...`, `--model_info_by_idx ...`, `--list_speaker_idxs`, `--list_language_idxs`, or `--source_wav --target_wav` for voice conversion. |
| `tts: command not found`. | Installed console entry point is not on `PATH`, or the wrong environment is active. | Activate/fix the package environment. Use [../scripts/check_tts_cli.py](../scripts/check_tts_cli.py) after the command is visible. Do not fall back to source-tree scripts. |
| `unrecognized arguments` or boolean parse errors. | Misspelled flag, wrong old flag name, or boolean value not accepted. | Re-run `tts --help`; use exact names such as `--model_path`, `--config_path`, `--vocoder_config_path`, `--speaker_idx`, `--language_idx`, `--pipe_out`. For boolean-like flags, prefer the flag alone when it supports an optional value, for example `--pipe_out`. |
| `--model_info_by_name` fails or reports missing model. | Name does not match registry grammar. | Run `tts --list_models` and copy the full listed name, including `tts_models/`, `vocoder_models/`, or `voice_conversion_models/`. |
| `--model_info_by_idx` points to the wrong model. | Registry indexes can change between package versions. | Prefer `--model_info_by_name` for reproducible instructions; use index only from the same `--list_models` output. |
| Released synthesis unexpectedly downloads files. | `--model_name` or an implicit default model triggers checkpoint resolution. | Treat released-model loading as a network/cache/disk action. If downloads are not allowed, use an already-cached model or custom `--model_path --config_path`. |

## Synthesis and model-loading failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Multi-speaker model asks for a speaker. | Model has multiple speakers and no `--speaker_idx` or `--speaker_wav` was provided. | Run `tts --model_name ... --list_speaker_idxs` after approving model load/download, then add `--speaker_idx`. For voice cloning models, provide one or more `--speaker_wav` files. |
| Multilingual model asks for a language or produces wrong language. | Missing or wrong `--language_idx`. | Run `tts --model_name ... --list_language_idxs` after approving model load/download, then pass an exact listed language id such as `--language_idx en`. |
| Voice-cloning command has `--speaker_wav` but no language. | Multilingual voice-cloning models often need both speaker reference and language. | Add `--language_idx ...` for CLI or route to [../../inference-and-model-zoo/SKILL.md](../../inference-and-model-zoo/SKILL.md) for Python API `language=` guidance. |
| Custom model cannot load. | `--model_path` and `--config_path` are missing, swapped, incompatible, or unreadable. | Supply both files, check existence/permissions, and confirm the config architecture matches the checkpoint. Use [../scripts/build_tts_command.py](../scripts/build_tts_command.py) with `--validate-paths` for local path checks. |
| Custom vocoder cannot load or audio quality is bad. | Missing `--vocoder_config_path`, incompatible vocoder, or mel/audio config mismatch. | Supply `--vocoder_path` and `--vocoder_config_path` together; verify sample rate, mel bins, hop length, and model family in [../../vocoder-and-audio-tools/SKILL.md](../../vocoder-and-audio-tools/SKILL.md). |
| `--speaker_wav` with multiple files behaves unexpectedly. | The CLI accepts one or more paths and averages the computed d-vectors. A bad file can spoil the reference. | Validate every referenced WAV path, duration, and sample format. Start with one known-good reference, then add more. |
| Voice conversion output sounds reversed. | `--source_wav` and `--target_wav` roles were swapped. | Use `--source_wav` for the audio to transform and `--target_wav` for the reference voice target. Route deeper checks to [../../voice-conversion/SKILL.md](../../voice-conversion/SKILL.md). |
| `--pipe_out` corrupts downstream text logs or audio player input. | WAV bytes are written to stdout. | Redirect stdout to an audio file/player and keep diagnostics on stderr. Avoid commands that parse stdout as text when `--pipe_out` is enabled. |
| CUDA flag/device confusion. | `--use_cuda True` is legacy and overrides `--device` to `cuda`; `--device cuda:0` is more explicit for synthesis CLI. | Prefer `--device cpu`, `--device cuda`, or `--device cuda:0`. Do not combine `--use_cuda True` with a conflicting `--device`. For server, only `--use_cuda` is exposed. |

## `tts-server` failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `tts-server: command not found`. | Console entry point is not on `PATH`. | Fix environment activation/installation, then run `tts-server --help`. Do not start source-tree server scripts. |
| `tts-server --help` fails before parser output. | Required server/runtime dependencies are missing. | Repair the installed package environment; server help imports Flask/config/model-manager dependencies in this version. |
| Server tries to download a model on launch. | Released `--model_name` or default model is not cached. | Decide whether downloads are allowed. If not, choose cached artifacts or custom `--model_path --config_path`. |
| `Address already in use` or launch hangs at startup. | Selected `--port` is already occupied, often default `5002`. | Pick a free `--port` or stop the old process. Record the port in the task handoff. |
| Server is reachable from more places than expected. | This version runs Flask on host `::`. | Treat launch as a network-binding action. Use local firewall/container/network controls; do not expose it as a public service by accident. |
| Debug server exposes tracebacks or reloads unexpectedly. | `--debug True` enables Flask debug behavior. | Keep `--debug False` unless actively debugging on a trusted local machine. Never use debug mode for shared demos. |
| Details page exposes configuration. | `--show_details True` renders model/config details. | Keep it false when sharing the server or when config paths/names are sensitive. |
| Custom checkpoint server launch fails. | Server custom flags are missing or old aliases were used. | Use `--model_path`, `--config_path`, `--vocoder_path`, `--vocoder_config_path`, and `--speakers_file_path`. This server version does not expose a custom language-id file flag. |

## Minimal diagnostics sequence

1. Run `tts --help` and `tts-server --help`.
2. Run [../scripts/check_tts_cli.py](../scripts/check_tts_cli.py) with checks limited to `help` if downloads or registry imports are not allowed.
3. Run `tts --list_models` and query a known metadata entry with `--model_info_by_name`.
4. Build the intended synthesis command with [../scripts/build_tts_command.py](../scripts/build_tts_command.py) before running it.
5. For server tasks, run [../scripts/check_tts_server_cli.py](../scripts/check_tts_server_cli.py), choose a free port, and launch only after explicit approval for model loading/downloads and network binding.
