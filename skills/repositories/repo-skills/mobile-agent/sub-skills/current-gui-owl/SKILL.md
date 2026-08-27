---
name: current-gui-owl
description: "Use current Mobile-Agent-v3.5 / GUI-Owl 1.5 phone, desktop, and
  browser workflows with safe command construction, configuration checks, and
  troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Current GUI-Owl / Mobile-Agent-v3.5

Use this sub-skill for current Mobile-Agent-v3.5 and GUI-Owl 1.5 workflows on Android phones/emulators, desktop computers, and browsers. It owns command construction and troubleshooting for live GUI agents, but it does not execute live device/browser/desktop actions by default.

## Route by platform

| Prompt signal | Workflow | Read / run |
|---|---|---|
| Android phone, ADB, ADB Keyboard, app open/tap/type/swipe, Mobile-Agent-v3.5 mobile | Mobile GUI-Owl | [`references/mobile-desktop-browser.md`](references/mobile-desktop-browser.md), `scripts/build_mobile_command.py` |
| Desktop GUI, local app, PyAutoGUI, screenshot/accessibility, computer-use | Desktop GUI-Owl | [`references/mobile-desktop-browser.md`](references/mobile-desktop-browser.md), `scripts/build_computer_command.py` |
| Browser/site/web task, Playwright, headless, CSS SoM, OmniParser, image_type, web login | Browser GUI-Owl | [`references/browser-agent.md`](references/browser-agent.md), `scripts/build_browser_command.py` |
| API/base URL/model/env-var config, max steps, missing DISPLAY/ADB/browser deps | Safe validation | `scripts/validate_gui_owl_config.py`, [`references/configuration.md`](references/configuration.md) |
| Tool-call parse failures, coordinates, typing, screenshots, browser asset upload | Troubleshooting | [`references/troubleshooting.md`](references/troubleshooting.md) |

## Safe workflow

1. Identify platform: `mobile`, `computer`, or `browser`.
2. Validate the configuration shape:

```bash
python sub-skills/current-gui-owl/scripts/validate_gui_owl_config.py \
  --platform mobile \
  --adb-path-env ADB_PATH \
  --api-key-env GUI_OWL_API_KEY \
  --base-url-env GUI_OWL_BASE_URL \
  --model-env GUI_OWL_MODEL \
  --instruction "Open Chrome and search Tongyi Lab" \
  --require-adb-keyboard
```

3. Build a command with a bundled script. Example mobile template:

```bash
python sub-skills/current-gui-owl/scripts/build_mobile_command.py \
  --repo-root-env MOBILE_AGENT_REPO \
  --adb-path-env ADB_PATH \
  --api-key-env GUI_OWL_API_KEY \
  --base-url-env GUI_OWL_BASE_URL \
  --model-env GUI_OWL_MODEL \
  --instruction "Open Chrome and search Tongyi Lab" \
  --device emulator-5554
```

4. Before running the printed command in a prepared runtime checkout, verify live prerequisites manually: device/display/browser availability, model endpoint health, and private credentials.

## Important facts

- Mobile and desktop launchers require `--api_key`, `--base_url`, `--model`, and `--instruction`.
- Mobile launcher also requires `--adb_path`, optional `--device`, and can use separate app-resolver API/base/model flags.
- Browser launcher uses task/web/browser/eval flags, `--image_type` (`base64`, `file`, or `oss`), `--headless`, `--use_css_som`, and `--use_omni_som`/`--omni_url`.
- GUI-Owl action coordinates are normalized `0..1000` and rescaled to screenshot width/height by the launcher.
- The mobile action parser expects a `<tool_call>` block containing JSON with nested `arguments`.

## Boundaries

- AndroidWorld, OSWorld, WebArena/WebVoyager/VisualWebArena, grounding/knowledge, and GUI-Critic evaluation belong to [`../benchmarks-and-evaluation/SKILL.md`](../benchmarks-and-evaluation/SKILL.md).
- Mobile-Agent-E task evolution and persistent tips/shortcuts belong to [`../mobile-agent-e/SKILL.md`](../mobile-agent-e/SKILL.md).
- PC-Agent's separate SoM/OCR/A11y desktop stack belongs to [`../pc-agent/SKILL.md`](../pc-agent/SKILL.md).
- Legacy v1/v2/v3 Mobile-Agent command preservation and migration belong to [`../legacy-agents/SKILL.md`](../legacy-agents/SKILL.md).
- UI-S1 training/evaluation/checkpoint workflows belong to [`../ui-s1-training/SKILL.md`](../ui-s1-training/SKILL.md).

## Do not

- Do not paste raw API keys into commands; use env vars.
- Do not claim live phone, browser, or desktop success from command-building or config validation alone.
- Do not run desktop control in a headless shell or Android control without explicit user authorization.
- Do not send users back to original repository scripts; use the bundled builders and references here.
