---
name: tui-and-desktop
description: "Router for terminal chat presentation, OpenTUI host behavior,
  plain fallback, Web UI presentation, and desktop packaging/runtime."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# TUI and Desktop

Use this sub-skill for the user-facing surface family: terminal chat, OpenTUI
host behavior, the Web UI control console, artifact previews, and the packaged
desktop shell.

## Route elsewhere
- Setup/install, gateway lifecycle, and release vs source installation choices
  → `setup-and-gateway`
- Provider/search/router/config issues surfaced in the UI →
  `configuration-and-routing`
- Chat/session automation without a UI focus → `cli-and-automation`
- Channels and MCP → `channels-and-integrations`
- Skill catalogs and meta-skills → `skills-and-meta`

## Covers
- `opensquilla chat --ui auto|tui|plain`
- OpenTUI source-development override and companion-host behavior
- Terminal resize, alternate-screen, and host crash recovery
- Web UI presentation, artifacts, deliverables, and preview behavior
- Desktop packaging/runtime and launch semantics

## Use these references
- `references/commands.md`
- `references/runtime-and-packaging.md`
- `references/artifact-previews.md`
- `references/troubleshooting.md`

## Safe helper
- `scripts/smoke_tui_host_companion.py` — tiny bridge smoke for an installed
  or source-host TUI companion

## Verification anchors
- `tests/test_cli/test_tui_meta_command.py`
- `tests/test_cli/test_help_theme.py`
- `tests/test_desktop/test_electron_startup_contract.py`
- `tests/functional/test_webui_browser_e2e.py`
- `opensquilla-webui/e2e/chat.spec.ts`
- `opensquilla-webui/e2e/artifact-card.spec.ts`
- `opensquilla-webui/e2e/artifact-preview.spec.ts`
- `opensquilla-webui/e2e/preview-origin-csp.spec.ts`
- `opensquilla-webui/e2e/session-drawer.spec.ts`
- `opensquilla-webui/e2e/settings-modal.spec.ts`
- `opensquilla-webui/e2e/workbench.spec.ts`
- `desktop/electron/scripts/test-native-workbench-surface.mjs`
- `desktop/electron/scripts/test-desktop-gateway-lifecycle.mjs`
- `desktop/electron/scripts/test-cli-invocation.mjs`

## Notes
- Keep provider/router/search questions out of this sub-skill unless the issue
  is visibly caused by a UI surface.
- Keep non-UI chat/session workflows out of this sub-skill unless the launch,
  renderer, or packaging behavior is the question.
