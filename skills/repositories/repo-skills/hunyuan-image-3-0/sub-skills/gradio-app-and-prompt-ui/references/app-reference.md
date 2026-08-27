# Gradio App Reference

This reference describes the interactive HunyuanImage-3.0 Gradio chat UI, its
launch wrapper, prompt controls, and image-history behavior. Use it for launch
planning and UI diagnostics. Use `local-inference-cli` when the user needs a
repeatable generation command instead of an interactive browser session.

## Launch layers

The UI has two launch layers:

1. A shell wrapper prepares environment variables, prepends the project root to
   `PYTHONPATH`, disables Gradio analytics, clears proxy variables used by
   Gradio/httpx, and forwards arguments to the Python app.
2. The Python app loads the HunyuanImage-3.0 app pipeline, builds a Gradio
   `Blocks` interface, and launches with `share=False`.

The current app path is not considered healthy in this snapshot because the app
pipeline still imports stale module names. See `references/troubleshooting.md`
before advising a user to launch the UI.

## Wrapper environment contract

| Variable | Meaning | Wrapper default | Notes |
| --- | --- | --- | --- |
| `MODEL_ID` | Local checkpoint directory passed as `--model-id` | placeholder model directory | Treat as required. A placeholder or missing path should stop launch planning. |
| `GPUS` | Comma-separated GPU ids copied to `CUDA_VISIBLE_DEVICES` | `0,1,2,3` | Actual generation still needs enough CUDA memory and a valid checkpoint. |
| `HOST` | Bind host passed as `--host` | `0.0.0.0` | Use `127.0.0.1` for local-only testing. |
| `PORT` | Bind port passed as `--port` | `443` | Port 443 may require elevated privileges; use 7860 or 8080 when binding fails. |
| `GRADIO_ANALYTICS_ENABLED` | Gradio analytics toggle | `False` | Set by the wrapper before launch. |
| `PYTHONPATH` | Python import path | project root prepended by wrapper | Lets the app import local modules from a checkout. |
| `http_proxy`, `https_proxy` | Proxy environment variables | cleared | The wrapper clears them to avoid Gradio/httpx timeout behavior. |

The Python parser's own port default is `8080`, but the shell wrapper overrides
it by passing the `PORT` environment value. Do not confuse these two defaults.

## Python app launch arguments

| Argument | Purpose | Notes |
| --- | --- | --- |
| `--host` | Server bind host | Wrapper default is `0.0.0.0`; local-only users often want `127.0.0.1`. |
| `--port` | Server bind port | Wrapper default is `443`; parser default is `8080`. |
| `--image-cache-dir` | Directory for generated image copies | When set, generated images are saved in date-based subdirectories. |
| `--open-sidebar` | Open the parameter sidebar by default | The wrapper passes this flag. |
| `--model-id` | Local checkpoint path | Required in practice. Use a local model directory, not an empty placeholder. |
| `--attn-impl` | Attention implementation | Choices are `sdpa` and `flash_attention_2`. |
| `--moe-impl` | MoE implementation | Choices are `eager` and `flashinfer`. |
| `--seed` | Generation seed | `-1` means choose a random seed inside the response function. |
| `--diff-infer-steps` | Diffusion inference steps | Defaults to the loaded model generation config when omitted. |
| `--diff-guidance-scale` | Diffusion guidance scale | Defaults to the loaded model generation config when omitted. |
| `--image-size` | Target image size | UI exposes `auto`, square, and common aspect-ratio presets. |
| `--bot-task` | Chat task mode | UI exposes `image`, `auto`, `think`, and `recaption`; the parser also accepts `img_ratio`. |
| `--context-mode` | History scope | `single_round` keeps the latest user turn; `unlimited` keeps all messages. |
| `--top-k` | Text-generation top-k | Defaults to the loaded model generation config when omitted. |
| `--top-p` | Text-generation top-p | Defaults to the loaded model generation config when omitted. |
| `--temperature` | Text-generation temperature | Defaults to the loaded model generation config when omitted. |
| `--use-system-prompt` | Prompt preset selector | UI choices are `None`, `dynamic`, `en_vanilla`, `en_recaption`, `en_think_recaption`, and `custom`. |

## UI layout and controls

The Gradio UI is message-based (`type="messages"`). It includes:

- A left sidebar with **Image Generation** controls: image size, seed,
  diffusion steps, guidance, system-prompt mode, bot task, and context mode.
- A collapsed **Text Generation** section with top-k, top-p, and temperature.
- A **System Prompt** accordion whose textbox is shown, hidden, or prefilled
  based on the selected system-prompt mode.
- A chat panel and a multimodal input box that accepts multiple image files and
  long text.
- Undo and retry actions connected to the chat history.

Prompt mode behavior in the UI:

- `None` hides the system-prompt textbox and sends no system prompt.
- `dynamic` picks a preset from the selected bot task: vanilla for `image`,
  recaption for `recaption`, and think+recaption for `think`.
- `en_vanilla`, `en_recaption`, and `en_think_recaption` show preset text.
- `custom` shows an editable empty textbox.

The UI dropdown is narrower than the full model-level prompt taxonomy. If the
user asks about non-UI prompt modes or `en_unified`, route to
`prompt-and-image-conditioning` or `core-apis-and-architecture`.

## Image and conversation-history handling

The app uses a message-list flow rather than a tuple-style chat history:

1. The multimodal input submits a dictionary with `text` and `files`.
2. Each uploaded image file is appended to history as a user image message.
3. The text prompt, when present, is appended after the uploaded images as a
   user text message.
4. Before generation, the history is converted into model messages.
5. Text messages become text entries. Gradio image components are converted to
   image-info objects through the app image processor.
6. A generation request is rejected if the final converted message is not from
   the user.
7. Text responses stream into the last assistant message. When image generation
   starts, the UI inserts a spinner and replaces it with the final image.
8. If an image cache directory was provided, generated images are saved under a
   date directory with timestamped PNG filenames.

Context-mode behavior:

| Mode | Behavior |
| --- | --- |
| `single_round` | Keep any initial system message, then keep only the final consecutive user messages. This is useful for a prompt plus uploaded image set. |
| `unlimited` | Preserve the full conversation, including prior assistant/user turns. Use it only when multi-turn context is intentional. |

Only text strings and Gradio image components are valid message content for the
current app pipeline. Other content objects lead to unsupported-message errors.

## When to use the UI instead of the CLI

Use the UI when the user needs:

- Interactive prompt exploration with visible system-prompt controls.
- Manual image uploads in a browser session.
- Undo/retry while inspecting streamed text and generated images.
- Quick adjustment of seed, image size, context mode, text-sampling controls,
  or prompt presets.

Prefer `local-inference-cli` when the user needs:

- A reproducible command line with a fixed prompt, seed, image size, and save path.
- Batch or scripted generation.
- A stable fallback while the UI import path is broken.
- Actual generation guidance without needing a browser server.

## Bundled helpers

- Run `scripts/render_gradio_launch.py --help` to see how to render a launch
  command without opening a port.
- Run `scripts/check_app_imports.py --help` to inspect the UI import surface and
  confirm the known stale-import diagnostics.
