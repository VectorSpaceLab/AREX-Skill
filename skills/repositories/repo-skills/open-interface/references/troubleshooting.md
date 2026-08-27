# Open Interface Troubleshooting Router

## Purpose

Read this root troubleshooting reference when the failure category is unclear.
It routes issues to the nearest bundled sub-skill reference and separates safe
static checks from manual GUI/API/build operations.

## First split: runtime or packaging?

| Symptom | Likely owner | Next step |
|---|---|---|
| API key, model selection, custom base URL, malformed JSON, screenshot, display, keyboard/mouse, Stop button, or request-loop failure | `sub-skills/desktop-runtime/` | Read `sub-skills/desktop-runtime/references/troubleshooting.md`; run `sub-skills/desktop-runtime/scripts/inspect_action_map.py` for contract checks. |
| PyInstaller missing import/resource, build option, release archive, version bump, codesign/notary, stale `dist/`/`build`, or platform package issue | `sub-skills/packaging/` | Read `sub-skills/packaging/references/troubleshooting.md`; run `sub-skills/packaging/scripts/build_preflight.py` for safe facts. |
| Packaged app launches but runtime automation fails | Both | Use packaging only to confirm modules/resources were bundled; then use desktop-runtime for credentials, permissions, screenshots, and JSON/action behavior. |
| Need a safe static check across both surfaces | Root | Run `python scripts/check_runtime_contract.py --pretty`, then the two sub-skill helpers relevant to the task. |

## Safe checks available from the generated skill

```bash
python scripts/check_runtime_contract.py --pretty
python sub-skills/desktop-runtime/scripts/inspect_action_map.py --pretty
python sub-skills/packaging/scripts/build_preflight.py --repo-root <target-checkout> --json
```

These helpers do not launch the GUI, use provider API keys, capture screenshots,
move the mouse/keyboard, run PyInstaller, sign, notarize, or create release
artifacts.

## Approval-required operations

Ask before:

- Installing or upgrading dependencies or system packages.
- Launching the GUI app, granting desktop permissions, or running live desktop
  automation.
- Using OpenAI, Gemini, or custom model provider API keys.
- Running source build helpers, PyInstaller, codesign, notarytool, stapler, or
  archive commands.
- Deleting or overwriting `dist/`, `build/`, `.spec`, zip, app, or executable
  artifacts.

## Common cross-cutting gotchas

- The app is script-style rather than a packaged Python distribution. Runtime
  facts are driven by source modules and dependencies, not distribution entry
  point metadata.
- PyAutoGUI imports and screenshot calls can fail in headless environments
  before any provider request is made.
- Provider JSON contract failures can look like automation failures; validate
  the `steps`/`done` schema before debugging mouse/keyboard behavior.
- PyInstaller may hide runtime resource problems until the packaged app starts;
  use packaging preflight first, then desktop-runtime diagnostics.
- Base64-encoded API keys in settings are sensitive; base64 is not encryption.
