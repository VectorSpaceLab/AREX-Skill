# Runtime and packaging

## Source checkout vs release

- Official wheels, desktop installers, and container images already include the
  built Vue control console.
- Source checkouts need Node.js 22.12+ and npm to build the Web UI.
- A missing or stale control console is a fail-closed build problem, not a
  runtime fallback.
- `pip install .`, `uv tool install .`, and VCS URL installs follow the same
  fail-closed rule.

## OpenTUI companion

- Current releases do not publish the full-screen OpenTUI companion.
- `auto` may fall back to plain; strict `tui` requires the host.
- The companion package is version-locked to the product and to
  `@opentui/core`.
- The current source-host toolchain is pinned: Bun 1.3.14, Node >=20.14, and
  `@opentui/core` 0.4.3.
- The build helper `scripts/build_tui_host_companion.py` is maintainer-only
  reference material; do not treat it as a runtime dependency.
- Same-version host/core mismatches should be fixed by rebuilding both from the
  same checkout, not by mixing release and source artifacts.

## Web UI package

```sh
cd opensquilla-webui
npm ci
npm run build
```

- `opensquilla-webui/package.json` requires Node >=22.12.0.
- Rebuild the Web UI after front-end or preview changes.
- `npm run build:artifact` is the packaged artifact build path; it should stay
  in step with the gateway-served console.

## Desktop shell

```sh
cd desktop/electron
npm ci
npm run dist:local
```

- The desktop shell reuses the same Vue frontend and Python gateway.
- Packaged builds launch the control console through the gateway and load
  `/control/chat/new` first.
- The shell runs with `contextIsolation: true` and `nodeIntegration: false`.
- `desktop/electron/package.json` pins Electron 42.4.0.
- The shell writes its state under Electron `userData` and starts a local
  gateway by default.
- For a faster rebuild after the frontend already exists, use
  `npm run build:web` and then `npm run dist`.
- `desktop/electron/scripts/test-*` remain maintainer harnesses; keep them out
  of the runtime helper set.

## Safe smoke helper

- `scripts/smoke_tui_host_companion.py` is the small runtime smoke for the
  companion lifecycle.
- Use it only when a companion is present or when you intentionally exercise
  the source-host path.
