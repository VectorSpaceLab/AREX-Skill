---
name: "app-agent"
description: "Routes AppAgent setup, exploration, and deployment workflows for
  Android-device task automation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# AppAgent

AppAgent operates Android apps through ADB, screenshot/XML capture, multimodal model calls, and generated UI documentation.

Use this skill when the task is about:
- installing or validating the AppAgent runtime prerequisites,
- generating UI documentation through autonomous exploration or human demonstration,
- running AppAgent against a documented app in deployment mode,
- debugging model/config/device issues in a local checkout.

## First read
- `references/setup.md` for Python, `adb`, device/emulator, and config prerequisites.
- `references/configuration.md` for the `config.yaml` keys and backend selection rules.
- `references/workflows.md` for the high-level exploration/deployment output layout.
- `references/troubleshooting.md` for the most common failures and recovery steps.
- `references/api-reference.md` when you need exact helper signatures or parser behavior.

## Quick preflight
Use the bundled checker before launching a real device session:
- `scripts/check_setup.py --repo-root <AppAgent checkout>`
- `scripts/check_setup.py --repo-root <AppAgent checkout> --skip-adb` when you only want Python/config validation.

The checker is read-only. It confirms imports, config keys, and whether `adb` is on `PATH`.

## Route map

### Setup and readiness
Use the setup references and `scripts/check_setup.py` when the request is about:
- installing dependencies,
- editing `config.yaml`,
- choosing OpenAI versus Qwen,
- connecting a phone or emulator,
- deciding where generated `apps/` and `tasks/` folders should live.

### Exploration
Use `sub-skills/exploration/SKILL.md` when the request is about:
- autonomous exploration,
- human demonstration capture,
- generating or refining UI docs,
- understanding the output under `apps/<app>/auto_docs/` or `apps/<app>/demo_docs/`.

The exploration launcher lives at:
- `sub-skills/exploration/scripts/start_exploration.py`

### Deployment
Use `sub-skills/deployment/SKILL.md` when the request is about:
- running a task against an app that already has docs,
- selecting between auto and demo docs,
- interpreting task logs and deployment outcomes,
- handling no-doc fallback decisions.

The deployment launcher lives at:
- `sub-skills/deployment/scripts/start_deployment.py`

## Common operating assumptions
- AppAgent expects a live Android device or emulator plus `adb`.
- The repo stores generated outputs under `apps/` and `tasks/` relative to the chosen `root_dir`.
- The repository is script-driven; the helpers and references in this skill are the public runtime contract.
- YAML config values are the effective source of truth for runtime settings.

## If something fails
- Check `references/troubleshooting.md` first.
- If the device is unavailable, fix the host/device layer before retrying the Python checks.
- If the multimodal backend or parser fails, inspect the raw logs in the generated `tasks/` or `apps/<app>/demos/` tree.
- If grid swipes behave oddly, remember the current precise-swipe bug and prefer the safer path until it is patched.

## What this skill does not do
- It does not train a new model.
- It does not replace the user's Android device or emulator.
- It does not assume the repo checkout is packaged as an installable Python distribution.
