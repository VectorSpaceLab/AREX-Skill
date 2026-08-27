# AppAgent configuration

This repo is controlled by `config.yaml` at the repository root. The helper `load_config()` loads environment variables first and then updates them with the YAML file, so YAML values win when keys overlap.

## Core keys

| Key | Meaning | Notes |
| --- | --- | --- |
| `MODEL` | Backend selector | Must be `OpenAI` or `Qwen` |
| `OPENAI_API_BASE` | OpenAI-compatible chat-completions URL | Used when `MODEL=OpenAI` |
| `OPENAI_API_KEY` | OpenAI API key | Required for OpenAI runs |
| `OPENAI_API_MODEL` | Vision-capable model name | README and source use `gpt-4-vision-preview` |
| `MAX_TOKENS` | Max completion tokens | Passed to the OpenAI request |
| `TEMPERATURE` | Sampling temperature | Lower values make the agent more consistent |
| `REQUEST_INTERVAL` | Seconds between model requests | Protects against rate limits |
| `DASHSCOPE_API_KEY` | DashScope API key | Required for `MODEL=Qwen` |
| `QWEN_MODEL` | Qwen multimodal model name | README suggests `qwen-vl-max` |
| `ANDROID_SCREENSHOT_DIR` | Remote device screenshot directory | Must exist on the Android device/emulator |
| `ANDROID_XML_DIR` | Remote device UI XML directory | Must exist on the Android device/emulator |
| `DOC_REFINE` | Whether to refine existing docs | `true` reuses and improves prior docs |
| `MAX_ROUNDS` | Exploration step cap | Prevents unbounded loops |
| `DARK_MODE` | Label overlay style | Affects screenshot annotation contrast |
| `MIN_DIST` | Minimum spacing between detected elements | Helps de-duplicate nearby UI nodes |

## Workflow-specific config behavior
- Exploration and deployment both need a valid model backend and a reachable device.
- Exploration writes documentation under `apps/<app>/auto_docs/` or `apps/<app>/demo_docs/`.
- Deployment reads from `apps/<app>/auto_docs/` or `apps/<app>/demo_docs/` and writes logs under `tasks/`.
- If no docs are present, deployment can proceed only after an explicit no-doc choice.

## Practical editing guidance
- Keep secrets in `config.yaml`; do not rely on ephemeral shell environment overrides for the same keys.
- Use a writable `root_dir` outside the repo when you want to keep generated outputs separate from the checkout.
- If you switch backends, update both `MODEL` and the matching key set in the same edit.
