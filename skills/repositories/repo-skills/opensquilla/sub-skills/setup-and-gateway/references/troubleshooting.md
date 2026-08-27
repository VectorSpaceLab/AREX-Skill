# Troubleshooting

## Start here

```sh
opensquilla doctor
opensquilla gateway status
opensquilla onboard status
```

If the gateway is running, the Web UI Health view also shows readiness and recovery hints.

## `opensquilla` command not found

After a fresh `uv tool install`, open a new terminal or run:

```sh
uv tool update-shell
```

Check what the shell sees with `command -v opensquilla` on macOS/Linux or `where.exe opensquilla` on Windows.

## Gateway is not running or the URL is wrong

Start the gateway again:

```sh
opensquilla gateway run
```

Or use the managed background process:

```sh
opensquilla gateway start --json
opensquilla gateway status
```

If the port is busy, use another one:

```sh
opensquilla gateway run --port 18792
```

If the browser cannot connect, make sure the host and port in the URL match the gateway bind.

## Web UI assets are missing or stale

This usually means a source checkout has not built the Vue console yet, or the console build is out of date.
Rebuild it from the checkout:

```sh
cd opensquilla-webui
npm ci
npm run build
```

If the user does not need to work from a checkout, install the official release wheel instead.

## Router dependencies are missing but direct mode still works

On Windows, ONNX Runtime may need the Visual C++ Redistributable for Visual Studio 2015–2022 x64.
On macOS terminal installs, LightGBM may need the system OpenMP runtime (`libomp`).

OpenSquilla can still run with direct single-model routing while those native libraries are missing.
Install the missing runtime, then restart the gateway.

```sh
opensquilla gateway restart
```

## Proxy environment warning

If the CLI warns that proxy variables are being ignored, set:

```sh
OPENSQUILLA_TRUST_ENV=1
```

That tells OpenSquilla to honor `HTTP_PROXY` and `HTTPS_PROXY` values from the shell.

## First-run setup variants

- `opensquilla onboard --if-needed` is the safe rerun path for scripts and reinstall flows.
- `opensquilla onboard --minimal` keeps onboarding to the core provider path.
- `opensquilla onboard status` shows which sections still need attention.

## Need a support snapshot

Use `opensquilla bundle` to collect a redacted diagnostics zip, especially when the gateway cannot start cleanly.
