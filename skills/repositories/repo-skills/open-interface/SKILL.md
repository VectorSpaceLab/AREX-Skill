---
name: open-interface
description: "Use Open Interface for LLM-driven desktop automation runtime,
  configuration, packaging, and safe repository maintenance workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Open Interface repo skill

Use this repo skill when a task is about Open Interface, the Python desktop app
that sends screenshots and user objectives to an LLM backend, receives JSON
instructions, and executes keyboard/mouse/wait steps to operate a computer.

This skill is self-contained guidance for future Open Interface checkouts. It
bundles safe diagnostics and distilled runtime/build knowledge; it does not
bundle the application source code, provider credentials, desktop permissions,
or release signing credentials.

## Quick routes

| Task signal | Read next |
|---|---|
| Run the app, configure API keys, choose GPT/Gemini/custom models, inspect the request loop, debug malformed `steps`/`done` JSON, map OpenAI computer-use actions, or troubleshoot screenshots/pyautogui/display permissions | [sub-skills/desktop-runtime/SKILL.md](sub-skills/desktop-runtime/SKILL.md) |
| Package or release the app, inspect PyInstaller options, hidden imports, resource inclusion, version bumps, Linux/Windows onefile behavior, macOS signing/notarization, or stale build artifacts | [sub-skills/packaging/SKILL.md](sub-skills/packaging/SKILL.md) |
| The symptom could be either runtime or packaging | [references/troubleshooting.md](references/troubleshooting.md) |
| Check whether this skill matches the current repository version | [references/repo-provenance.md](references/repo-provenance.md) |

## Safe first checks

These bundled helpers are designed for inspection. They do not launch the GUI,
use provider API keys, move the mouse/keyboard, capture screenshots, run
PyInstaller, sign, notarize, or create release artifacts.

```bash
python scripts/check_runtime_contract.py --pretty
python sub-skills/desktop-runtime/scripts/inspect_action_map.py --pretty
python sub-skills/packaging/scripts/build_preflight.py --repo-root <target-checkout> --json
```

Use a target checkout only for source/build preflight facts. Do not point these
helpers at private files containing credentials.

## Runtime prerequisites summary

For normal app use in a target Open Interface checkout:

- Python 3.12 or newer is the documented script baseline.
- Runtime dependencies come from the project's dependency pins and include
  OpenAI, Google GenAI, Pillow, PyAutoGUI, ttkbootstrap, and platform-specific
  GUI/audio/build dependencies.
- A real interactive desktop is required for screenshots and keyboard/mouse
  automation. Headless sessions are suitable only for bundled static helpers.
- Model provider settings need an OpenAI, Gemini, or compatible custom endpoint
  API key. Settings changes require app restart.
- macOS runtime use requires Accessibility and Screen Recording permissions.

See the desktop-runtime sub-skill for detailed provider, settings, and JSON
contract guidance.

## Packaging prerequisites summary

For packaging or release planning:

- Start with the bundled packaging preflight helper rather than running the
  source build helper directly.
- Full builds can install dependencies, run PyInstaller, create/overwrite
  artifacts, prompt interactively, and use platform credentials.
- macOS signing/notarization requires private operator state; keep identities,
  keychain profiles, Apple credentials, and notary logs out of skill files and
  public reports.

See the packaging sub-skill for exact PyInstaller option expectations and safe
release boundaries.

## Approval boundaries

Ask before performing any operation that:

- Launches the GUI, captures screenshots, or controls the real keyboard/mouse.
- Sends requests to OpenAI, Gemini, or a custom model provider.
- Installs or upgrades dependencies or system packages.
- Runs PyInstaller or the source build helper.
- Deletes, overwrites, signs, notarizes, or archives build artifacts.
- Reads, writes, or displays secrets such as API keys or signing credentials.

## Refresh and import notes

- Read [references/repo-provenance.md](references/repo-provenance.md) before
  relying on this skill for a different commit or changed checkout.
- Structured router metadata for managed imports is in
  [references/repo-routing-metadata.json](references/repo-routing-metadata.json).
- This production run was configured not to import the skill automatically.
  Import later only after verification approval and the repo-skill locked import
  helper are used by the verification workflow.
