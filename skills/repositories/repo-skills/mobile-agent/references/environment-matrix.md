# Environment Matrix

Do not install all MobileAgent requirement files into one global environment. The repository contains Android control, desktop GUI automation, Playwright browser control, evaluation harnesses, legacy perception stacks, and UI-S1/verl distributed training dependencies that can conflict or require different hardware.

## Minimum verified construction scope

The generated skill was constructed and verified for safe CPU-oriented operating guidance:

- Static Markdown/link/frontmatter checks.
- Command-builder parser/help/fixture checks.
- JSON/config validator checks.
- Safe source import/metadata inspection where dependencies were available.

This scope does not claim live success for device control, browser sessions, paid APIs, benchmarks, model inference, checkpoint loading, or training.

## Runtime environment families

| Route | Main dependencies | Live external prerequisites | Safe CPU substitute | Notes |
|---|---|---|---|---|
| current-gui-owl mobile | Python, PIL, OpenAI-compatible client deps, ADB platform tools | Android device/emulator, USB debugging, ADB Keyboard, API key/base URL/model | command/config validation only | Do not treat `adb` availability as device authorization. |
| current-gui-owl desktop | Python, PIL, PyAutoGUI-like desktop deps | Unlocked GUI session, screenshot/accessibility permissions, API service | config validation only | Headless shells cannot prove desktop control. |
| current-gui-owl browser | Python, Playwright/Chromium, browser deps | Website access/login, model API, optional OSS/OmniParser | command validation only | Headless browser still needs Playwright install and system libraries. |
| AndroidWorld | `android_world`, absl flags, emulator tooling | Android emulator/device ports, one-time emulator setup, API service | command/import planning only | Live benchmark scoring is skipped without emulator/API. |
| OSWorld | OSWorld/VM stack and model API | VM image, environment config, display/automation service, API | command planning only | Do not run VM workflows during safe checks. |
| Web benchmarks | Playwright/browser stack, task service URLs, judge API | WebArena/WebVoyager/VisualWebArena services, login/session data, API/judge model | command validation only | Keep secrets out of commands. |
| GUI-Critic/grounding/knowledge | Transformers/VLM stack, datasets, checkpoints, optional CUDA | Model checkpoints, dataset paths, GPU/API budget | JSONL schema validation only | Replace hard-coded or sample keys with env variables. |
| Mobile-Agent-E | PyTorch plus Android/mobile perception deps | Android device/ADB, model services, persistent memory files | task JSON validation and command building | Evolution mode writes persistent tips/shortcuts under run logs. |
| PC-Agent | Desktop automation, OCR, SoM, API client deps | Mac/Windows GUI session, accessibility/screen recording, OCR/API credentials | config validation and command building | Ratio/font defaults differ between Mac and Windows. |
| legacy-agents | Older Mobile-Agent deps, possible GroundingDINO/CLIP/TF/ModelScope stacks | ADB/HDC device, hosted service or local models, credentials | command/config validation only | Prefer hosted v1 if avoiding local legacy perception stack. |
| UI-S1 | PyTorch, verl, Ray, vLLM/SGLang, flash-attn, Transformers, Hydra | CUDA GPUs, checkpoints, trajectory data, ports, logging services | JSONL validation and command building | Laptop/CPU-only hosts cannot verify training. |

## Practical setup policy

1. Choose the route first; do not install monorepo-wide dependencies.
2. Create a private environment per runtime family when live execution is required.
3. Install only that route's requirements plus documented optional backends.
4. Run command builders and validators before live commands.
5. Promote optional live checks to required only when the user asks to prove that capability.
6. Record skipped live checks as `SKIP_UNSAFE` or a required-backend block; never count them as passes.
