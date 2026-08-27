# Troubleshooting

## `--ui auto` fell back to plain

- This is expected on release installs because the OpenTUI companion is not
  published there yet.
- On a verified source checkout, the launcher may print the source-host
  commands and continue in plain mode for that launch. Wheels and source
  archives without a Git worktree stay quiet.
- If the fallback is unexpected, run `opensquilla doctor` to see the reason.

## `--ui tui` fails immediately

- Strict `tui` means the host is required.
- Check that Bun is installed, `@opentui/core` is present, and the companion
  and product versions match.
- Rebuild both from the same checkout if you have mixed source and release
  artifacts.
- Use `opensquilla chat --ui plain` while you repair the host path.

## The terminal looks broken after a crash or resize

- The host crash path restores the terminal and exits; it does not hot-switch
  to another renderer mid-turn.
- Repaint with `Ctrl+L` or relaunch the session.
- If the issue repeats, stay in plain mode and check the host availability and
  terminal support path first.

## The Web UI is missing or stale

- Rebuild the front-end: `cd opensquilla-webui && npm ci && npm run build`.
- For desktop packaging, rebuild the web UI before `npm run dist:local`.
- A missing or stale control console is a build failure; do not ship an empty
  `/control/` page.

## Desktop startup says a profile or gateway is already in use

- Stop the existing desktop app or gateway cleanly before retrying.
- Do not delete profile lock files.
- If the desktop shell recovered a verified orphan gateway, let the ownership
  check finish instead of force-spawning a second instance.

## Source-dev toolchain mismatch

- The TUI host path is pinned to Bun 1.3.14 and `@opentui/core` 0.4.3.
- Web UI and desktop source builds require Node.js 22.12+.
- Desktop packaging uses Electron 42.4.0.
- If any of those drift, rebuild from the matching checkout instead of mixing
  package versions.

## Preview or artifact problems

- Check whether offline preview is active, whether the resource actually exists,
  and whether a privileged gateway URL is being loaded from an isolated
  preview.
- If the Desktop preview cannot show a link, open it externally.
- If an artifact preview is unexpectedly blank, confirm that
  `OPENSQUILLA_PREVIEW_FORCE_OFFLINE` is not forcing a mode you did not want.
