# Docker and Compose Operations

## What the repository container path supplies

The container material describes a Python 3.10 image with system packages for
Xvfb/browser support, an isolated environment, Playwright-related variables,
and a helper named `xvfb-python`. Compose defines an `owl` service, exposes port
`7860`, sets `DISPLAY=:99`, configures `GRADIO_SERVER_NAME=0.0.0.0` and
`GRADIO_SERVER_PORT=7860`, mounts a private `.env`, an examples directory, and
an optional data directory, and requests `2gb` shared memory.

These are deployment evidence, not guarantees that a particular host's Docker
daemon, image, browser binary, or mount layout is ready.

## Safe preflight

1. Run `check_docker_runtime.sh --env-file <protected-env-file>` from any
   directory. It only reports whether Docker/Compose are reachable and whether
   selected values look present; it does not reveal values or change state.
2. Confirm the target owns the private env file and that the chosen host port is
   free. Do not mount a user home directory or broad project directory solely to
   make a workflow convenient.
3. Confirm Docker has enough disk/memory and that the expected browser workload
   has an X server/Xvfb path. Increase shared memory only with a justified host
   resource decision.
4. Build or pull an image only after accepting network transfer, cache, and
   service-start side effects. Run an explicitly chosen command against the
   deployment's own compose file; do not assume a generic Docker command will
   reproduce a source-specific layout.
5. After a container starts, run one minimal provider/config check before a
   browser or long multi-agent task. A successful container health check does
   not prove provider credentials or Playwright browser binaries work.

## Important source discrepancies

The Dockerfile's working directory and welcome text refer to Python example
files in a layout that is not identical to the current top-level `examples/`
directory, and the source run wrapper also assumes checkout-relative locations.
Do not copy those wrapper paths into a reusable deployment. Instead, map the
installed OWL package, protected configuration, example/worker code, and data
explicitly in the deployment you control.

## Browser display

The image creates an `xvfb-python` command that runs Python under `xvfb-run`.
Use it only for a workflow that needs a display. For ordinary provider or local
document checks, avoid launching a browser. For headless browser automation,
configure the relevant `BrowserToolkit` setting and prepare Playwright browsers
according to the selected runtime's policies.

## Stop conditions

Do not build/start a Compose stack from a troubleshooting loop that only needs
to inspect a file or import OWL. Stop and request permission when the next step
would pull an image, build dependencies, change Docker volumes, start a
long-running service, or expose a port outside the intended host boundary.
