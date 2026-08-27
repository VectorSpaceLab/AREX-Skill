# MusicAgent troubleshooting

## Fast triage

1. Validate the YAML first.
2. Confirm the launch directory and `local_fold` layout.
3. Check whether the failing tool is actually loaded.
4. Check secrets or API access only after the path/layout checks pass.

## Common failures and fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| Config parse fails | YAML syntax error or missing key | Run the bundled validator and repair the config before launching. |
| `semantic_kernel` import or connector errors | Old and new Semantic Kernel APIs do not always match | Use an isolated environment and install a version that still exposes the OpenAI/Azure text-completion classes expected by the wrapper. |
| `numpy`/`protobuf`/`librosa` breakage | Shared environment has a newer incompatible stack | Keep `numpy==1.23.0` and `protobuf==3.20.3` in a dedicated MusicAgent environment. |
| CLI cannot read OpenAI or Azure settings | `.env` missing or `use_azure_openai` does not match the secret set | Populate the `.env` values expected by the chosen backend. |
| Gradio starts but no chat window appears | OpenAI key not accepted | Enter a valid OpenAI key in the browser prompt. Gradio does not use the Azure path. |
| `No available models on ...` | The planner selected a task with no loaded pipe | The task vocabulary exists, but the loader does not instantiate a matching pipe. Use a supported task or extend the plugin registry. |
| `unloaded models on ...` | The pipe key is disabled or its cache is absent | Remove the pipe key from `disabled_tools` and restore the corresponding cache under `local_fold`. |
| Audio previews fail | `lilypond`, `midi2ly`, or `ffmpeg` missing | Install the system packages listed in the setup reference. |
| Audio loading or writing fails | `libsndfile1-dev` / `soundfile` stack missing | Install the audio system libraries before retrying. |
| ROC lyric-to-melody import fails | ROC helper tree is incomplete | Make sure the ROC support code is present under `local_fold/muzic/roc`, not just the adapter pair. |
| `fluidsynth` synthesis fails | Soundfont or command not present | Place `MS Basic.sf3` in the MusicAgent working directory and verify the `fluidsynth` binary is available. |
| `demucs` or `basic-pitch` fail immediately | The CLI tool is not installed or the path contains shell-sensitive characters | Install the helper package and use simple ASCII filenames without spaces. |
| GPU-oriented tool fails on CPU-only host | The tool initializer expects CUDA or a large model cache | Disable that pipe or move to a CUDA-capable runtime. |
| Spotify or Google tools return HTTP/auth errors | Credentials or network access missing | Add the required API credentials, verify quotas, or disable the tool. |
| Gradio exposes a public link | The demo launches with `share=True` | Use the CLI or wrap the launcher locally if you need a private-only session. |

## Tool-selection notes

- `disabled_tools` is compared with the pipe keys, not the planner task names.
- `candidate_tools` only matters when more than one pipe can serve a task.
- Some planner tasks are intentionally aspirational in the current wrapper snapshot. They will only work after the plugin layer is extended.
- If the wrong result appears, inspect the task name first, then the loaded pipe list, then the relevant credential or model cache.

## Safe debug checklist

- Confirm the config still resolves `local_fold` to the expected model cache tree.
- Confirm `src_fold` is writable; the wrapper stores uploads and generated media there.
- Confirm `MS Basic.sf3` is present when symbolic-to-audio or MIDI rendering is involved.
- Keep untrusted audio URLs out of the Gradio flow unless you want the app to download them.
