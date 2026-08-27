---
name: desktop-runtime
description: "Run, configure, inspect, and troubleshoot Open Interface desktop
  automation runtime workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Open Interface desktop runtime sub-skill

Use this sub-skill when the task concerns running the Open Interface app,
configuring model providers and settings, understanding how natural-language
requests become desktop actions, debugging the LLM JSON contract, or diagnosing
screen/keyboard/mouse automation failures.

Do not use this sub-skill for PyInstaller builds, signing, release archives, or
version packaging checklists; route those tasks to `../packaging/`.

## Safety boundary

Automated-safe work:

- Read the bundled runtime references in this sub-skill.
- Run the bundled contract helper:
  `python scripts/inspect_action_map.py --pretty`.
- Validate a saved JSON response or computer-use action with
  `python scripts/inspect_action_map.py --input-json sample.json --pretty`.
- Inspect code or configuration structure without launching the GUI, taking
  screenshots, sending provider API requests, or moving the real mouse/keyboard.

Manual or approval-required work:

- Launching the GUI app, granting Accessibility or Screen Recording
  permissions, testing screenshot capture on a real desktop, or executing
  keyboard/mouse automation.
- Entering or using OpenAI, Gemini, or custom provider API keys.
- Running live tasks such as opening Chrome or editing user documents.
- Running the repository's GUI smoke test; it queues real user requests and
  requires a display plus configured model credentials.

## Routing checklist

1. Classify the issue:
   - "How does Open Interface work?" or "Which class owns this behavior?" → read
     [references/api-reference.md](references/api-reference.md).
   - "How do I configure keys, model names, base URL, browser, theme, or custom
     guidance?" → read [references/configuration.md](references/configuration.md).
   - "How do I run or manually smoke-test the app safely?" → read
     [references/workflows.md](references/workflows.md).
   - "The app loops, returns malformed JSON, cannot screenshot, lacks DISPLAY,
     cannot use a provider, or runs the wrong action" → read
     [references/troubleshooting.md](references/troubleshooting.md) and run the
     bundled contract helper before attempting live automation.
2. Keep model-provider and GUI tests separated. A valid JSON contract can be
   checked without API credentials or desktop control.
3. If a live desktop action is needed, confirm the target OS permissions,
   display, active application/window, API key, and stop/interrupt plan before
   execution.
4. If a runtime problem happens only after packaging, collect the runtime
   symptom here, then route PyInstaller resource or hidden-import analysis to
   `../packaging/`.

## Bundled materials

- [references/api-reference.md](references/api-reference.md) — component map,
  key classes/functions, LLM response schema, provider routing, interpreter
  behavior, and computer-use action mapping.
- [references/configuration.md](references/configuration.md) — settings file
  shape, API-key handling, model/base URL choices, browser/theme/custom
  guidance options, dependency notes, and restart requirements.
- [references/workflows.md](references/workflows.md) — safe runtime inspection,
  manual launch flow, request loop, stop/retry behavior, and manual GUI test
  boundaries.
- [references/troubleshooting.md](references/troubleshooting.md) — concrete
  symptoms, causes, and recovery steps for provider, JSON, screenshot, display,
  permissions, pyautogui, loop, and multi-monitor failures.
- [scripts/inspect_action_map.py](scripts/inspect_action_map.py) — standalone
  validator for built-in OpenAI computer-use action mappings and saved LLM JSON
  response schema; it never imports pyautogui, launches the GUI, screenshots, or
  calls provider APIs.
