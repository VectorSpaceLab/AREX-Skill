# Gradio App Troubleshooting

The Gradio UI is optional in this snapshot. Treat startup failures as a reason
to route users to `local-inference-cli` unless they explicitly want to patch or
investigate the app path.

## Startup and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Python stops before help output at `import gradio` | The active interpreter lacks the UI dependency | Use a Gradio-capable environment before diagnosing app-specific imports. The verified environment used Gradio 6.17.3. |
| Traceback mentions `hunyuan_image_3.hunyuan` | Stale app import path for `HunyuanImage3ForCausalMM` | Current package code exposes the model class from the canonical model module, not `hunyuan_image_3.hunyuan`. Treat the app as broken until patched. |
| Traceback mentions `hunyuan_image_3.tokenizer_wrapper` | Stale app import path for `ImageInfo` | `ImageInfo` is defined in the tokenization module, not in `hunyuan_image_3.tokenizer_wrapper`. Treat the app as broken until patched. |
| `python app/run_chatbot.py --help` never reaches the parser | Top-level imports run before argument parsing | Do not assume `--help` proves parser health. Use `scripts/check_app_imports.py` for safe import diagnostics. |
| User asks for a working image-generation path while the app is broken | UI is optional and currently blocked | Route to `local-inference-cli`; do not use the package console script as a fallback in this snapshot. |

A source-compatible patch would need to update the app pipeline imports, but this
sub-skill does not own patching or low-level architecture guidance. Route import
path details to `core-apis-and-architecture`.

## Model path and launch environment

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Launch request has no `MODEL_ID` | The shell wrapper's default model path is only a placeholder | Stop and ask for a real local checkpoint directory. `scripts/render_gradio_launch.py` intentionally rejects missing model paths. |
| `MODEL_ID` points to a non-existent directory | Checkpoint was not downloaded or was renamed | Correct the path before launch. For repeatable generation without the UI, use `local-inference-cli`. |
| Port binding fails on `443` | Port 443 is privileged on many systems or already in use | Set `PORT` to an unprivileged port such as `7860` or `8080`. |
| UI is exposed on all interfaces unexpectedly | `HOST=0.0.0.0` binds externally | Use `HOST=127.0.0.1` for local-only testing. |
| The app starts with the wrong GPUs | `GPUS` was not set or was inherited from the shell | Set `GPUS` explicitly; it becomes `CUDA_VISIBLE_DEVICES`. |

## Conversation-history failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Error says `The last message must be from user` | The converted history ends in an assistant message | Append a new user prompt, retry from a user turn, or clear the assistant-only tail before generation. |
| Earlier system prompt is ignored | The app only preserves a system message at the beginning | Move the system prompt to the initial position or use the UI system-prompt control. |
| User expects multi-turn memory but the model sees only the latest prompt | `context_mode=single_round` keeps only the initial system prompt plus final consecutive user messages | Use `context_mode=unlimited` only when full conversation context is intentional. |
| Retry replays the wrong context | Retry uses history up to the selected message index | Confirm the retry point and final user message before resubmitting. |

## Image-message handling

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Uploaded images are not used | They were not submitted through the multimodal image input | Use the UI image upload control; the app expects Gradio image components, not arbitrary objects. |
| Unsupported message type error | History content is neither a text string nor a Gradio image component | Normalize the history before calling the app pipeline. |
| Generated images are not saved to disk | `--image-cache-dir` was not provided | Provide an image cache directory if local copies are required. |
| User wants deterministic file output | The UI is interactive and cache filenames are timestamped | Route to `local-inference-cli` for explicit `--save` behavior. |

## UI versus CLI decision rule

Use the UI for interactive browser-based exploration, image uploads, undo/retry,
and live parameter tweaking. Use `local-inference-cli` for reproducibility,
scripted runs, explicit save paths, and any production guidance while the app
imports remain stale.
