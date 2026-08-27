# Install and First Run

## Choose the install path

| Path | Use when | What you need |
| --- | --- | --- |
| Release wheel | Normal terminal installs and first-time users | Python 3.12+ and `uv` |
| Source install | Running from a checkout or rebuilding the Web UI | Python 3.12+, Git, Git LFS, Node.js 22.12+, npm, and `uv` |

The release wheel already includes the built Web UI, so it does not require Node.js or npm on the user's machine.

## Recommended release install

```sh
uv tool install --python 3.12 "opensquilla[recommended] @ https://github.com/opensquilla/opensquilla/releases/download/v0.5.3/opensquilla-0.5.3-py3-none-any.whl"
```

Use the versioned wheel URL when you want a pinned release. The recommended extra includes the router and the default memory/search support.

If `opensquilla` is not found after install, open a new terminal or run `uv tool update-shell`.

## Source install

Use the source path only when the user is working from a Git checkout and expects the Web UI build to happen locally.

```sh
git lfs install
git clone https://github.com/opensquilla/opensquilla.git
cd opensquilla
git lfs pull --include="src/opensquilla/squilla_router/models/**"
bash scripts/install_source.sh
```

Windows PowerShell uses the matching installer script:

```powershell
powershell -ExecutionPolicy Bypass -File ./scripts/install_source.ps1
```

Both source installers rebuild the Vue control console before installing Python. If the user is developing from source instead of using the installer, the equivalent manual build is:

```sh
cd opensquilla-webui
npm ci
npm run build
```

## First-run workflow

1. Run `opensquilla onboard` for the guided setup.
2. Use `opensquilla onboard --if-needed` for scripts and reinstalls.
3. Use `opensquilla onboard --minimal` when the user wants the core setup path without the optional sections.
4. Use `opensquilla onboard --provider <id> --api-key-env <ENV_VAR>` for non-interactive provider setup.
5. Check `opensquilla onboard status` before starting the gateway if the setup state is unclear.
6. Start the gateway with `opensquilla gateway start --json` or `opensquilla gateway run`.
7. Open `http://127.0.0.1:18791/control/` after the gateway reports readiness.

## Readiness checklist

- `opensquilla onboard status` reports that onboarding is complete or points to the remaining section.
- `opensquilla gateway start --json` returns a live URL and readiness result.
- `opensquilla gateway status` succeeds for the current host and port.
- `opensquilla doctor` reports ready or explains what still needs attention.
- The Web UI loads at `/control/`.

## When to collect a bundle

Run `opensquilla bundle` when the user needs a redacted diagnostics zip for support or when the gateway will not start and they need to preserve the current state before changing it.
