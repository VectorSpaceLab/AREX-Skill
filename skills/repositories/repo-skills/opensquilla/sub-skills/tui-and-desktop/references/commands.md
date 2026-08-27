# Commands and UI selection

## Public `chat` modes

| Mode | Command | Behavior |
| --- | --- | --- |
| `auto` | `opensquilla chat` or `opensquilla chat --ui auto` | Uses OpenTUI when a compatible host is available before alternate-screen startup; otherwise falls back to plain. |
| `tui` | `opensquilla chat --ui tui` | Strict full-screen TUI. Missing or incompatible host is a startup error. |
| `plain` | `opensquilla chat --ui plain` | Minimal rescue renderer over the same runtime contracts. |

## Chat launch notes

- `opensquilla chat --standalone` runs direct terminal chat without the gateway.
- In gateway mode, chat is interactive only; use `opensquilla agent -m '...'` for
  non-TTY automation.
- `opensquilla doctor` explains which chat surface `--ui auto` selects on the
  current terminal and why a fallback happened.
- `opensquilla gateway run` and `opensquilla gateway start --json` are the
  normal entry points for the Web UI control console.

## Source-host override

```sh
bun install --frozen-lockfile --cwd=src/opensquilla/cli/tui/opentui/package
OPENSQUILLA_TUI_DEV_SOURCE_HOST=1 uv --directory <repo-root> run opensquilla chat --ui tui
```

- `OPENSQUILLA_TUI_DEV_SOURCE_HOST=1` explicitly selects the source host during
  development.
- This path is only for a verified source checkout with the host package
  installed; release wheels should stay on plain.
- `OPENSQUILLA_TUI_BACKEND` is an internal handoff between the public selector
  and the runtime adapters; do not ask users to set it directly.

## Helpful keys

- `Ctrl+O` expands or collapses the retained thinking/tool detail.
- `Ctrl+L` forces a clean repaint.
- `Ctrl+G` or `Ctrl+End` jumps back to the latest output after scrolling.
- `Tab` queues the draft; `Enter` submits or steers according to turn state.

## Preview and recovery switches

- `OPENSQUILLA_PREVIEW_FORCE_OFFLINE=1` disables full-network artifact previews.
- `OPENSQUILLA_TUI_REPAINT_WATCHDOG_MS` is diagnosis-only and should stay unset
  unless you are troubleshooting a host repaint path.
- `opensquilla chat --ui plain` is the safest fallback when diagnosing a host
  startup problem or terminal recovery issue.
