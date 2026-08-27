# Cross-Cutting Troubleshooting

## Route-selection problems

- If a user says "MobileAgent" plus Android/desktop/browser but no version, use current GUI-Owl v3.5.
- If the user says evolution, persistent tips, shortcuts, or task-list memory, route to Mobile-Agent-E.
- If the user says PC-Agent, SoM, OCR, Mac, Windows, A11y, or desktop ratio, route to PC-Agent rather than GUI-Owl desktop.
- If the user says AndroidWorld, OSWorld, WebArena/WebVoyager/VisualWebArena, GUI-Critic, grounding, knowledge benchmark, or score, route to benchmarks-and-evaluation.
- If the user says UI-S1, verl, GRPO/DAPO/PPO, Ray, vLLM, checkpoint merge, or SOP/AndroidControl JSONL, route to UI-S1.
- If the user names v1/v2/v3, HDC/HarmonyOS, `run_api.py`, `coor_type`, or `notetaker`, start with legacy-agents.

## Credentials and privacy

- Use environment variables for API keys/tokens, e.g. `GUI_API_KEY`, `MOBILE_AGENT_TOKEN`, `QWEN_API_KEY`, `OCR_ACCESS_KEY_ID`, and `OCR_ACCESS_KEY_SECRET`.
- Do not paste raw keys into commands, logs, JSON fixtures, or task reports.
- Treat sample keys in repo configs as placeholders; replace or redact them before sharing.
- For GUI-Critic-style online scoring, rewrite local scoring wrappers to read keys from environment variables before any live model/API call.

## Device and GUI availability

- ADB/HDC command presence is not the same as device authorization. Check `adb devices` or HDC equivalent in the live runtime environment before running agents.
- Android typing tasks require ADB Keyboard or equivalent input-method setup; tap/swipe may work while text entry fails.
- Desktop automation requires an unlocked visible session and OS screenshot/accessibility permissions. Headless CI cannot prove PyAutoGUI/desktop control.
- Browser headless mode still requires Playwright browser installation and system libraries. Headless does not remove API, login, website, or screenshot requirements.

## Model output/action parsing

- GUI-Owl v3.5 actions are parsed from `<tool_call>` JSON with nested `arguments`; ask the model to output exactly one tool call when parsing fails.
- GUI-Owl and Qwen-style coordinates are normalized `0..1000`; executors rescale them to screenshot pixels.
- PC-Agent has separate action/coordinate handling; inspect ratio, font path, SoM, OCR, and accessibility settings before blaming the model.

## Backend verification language

- `PASS` means a safe command/check actually ran and matched the generated skill guidance.
- `SKIP_UNSAFE` means a live device/browser/API/model/GPU/benchmark/training workflow was intentionally not run.
- `BLOCKED_REQUIRED_BACKEND` applies only if a requested required capability cannot be verified without a backend and no full CPU substitute exists.
- Safe command builders and validators verify guidance and schemas; they do not verify live execution.

## When to narrow scope

If the user asks for proof of a live capability, require the missing backend/service explicitly. Examples: Android device/emulator for phone/AndroidWorld, GUI display for desktop/PC-Agent, Playwright/services for browser benchmarks, GPU/checkpoints for grounding/UI-S1 training, and API keys/base URLs for model calls.
