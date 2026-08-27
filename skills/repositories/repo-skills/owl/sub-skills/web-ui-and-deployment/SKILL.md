---
name: web-ui-and-deployment
description: "Guides OWL's English Gradio interface, environment-file
  management, Docker Compose deployment, Xvfb, and browser-runtime
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OWL Web UI and Deployment

Use this route for the English Gradio UI, API-key configuration through the
interface, Docker/Compose, Xvfb, Playwright, ports, mounts, or container
troubleshooting. It is an operational route, not a promise that a server or
Docker daemon is available.

## Local UI path

1. Install OWL and its declared dependencies in Python 3.10–3.12.
2. Create a private environment file from the package's documented template,
   fill only the provider and tool keys needed by the selected workflow, and
   keep it outside version control.
3. Run the English web application from the project layout expected by the
   source script. The implementation uses a script-oriented absolute import
   for `utils`, so do not assume `import owl.webapp` from an arbitrary current
   directory is equivalent.
4. Read [web-ui-reference.md](references/web-ui-reference.md), then use
   [check_web_ui_config.py](scripts/check_web_ui_config.py) to compare the
   selected example module names with the files actually present before
   submitting a request. The UI's module description table can contain names
   not present in a particular checkout.
5. Enter a nonblank task, select a module that exports the expected
   `construct_society` interface, and inspect the status/token/log output. Route
   provider construction to [workforce-workflows](../workforce-workflows/SKILL.md).

The UI can initialize, read, update, and delete `.env` values. Treat those
callbacks as mutations: do not paste secrets into prompts or logs, and prefer
shell environment variables or a protected file when policy disallows UI
writes.

## Container path

Read [docker-operations.md](references/docker-operations.md) before using
Compose, and run [check_docker_runtime.sh](scripts/check_docker_runtime.sh) for
non-mutating host diagnostics. The supported pattern uses a service exposing
port 7860, a mounted
`.env`, example/data mounts, large shared memory for browser work, and an
Xvfb-backed Python command where a display is required. Build and image pulls
are networked and potentially expensive; the bundled checker only diagnoses
the host and never starts or builds a container.

Use [troubleshooting.md](references/troubleshooting.md) for stale module names,
port conflicts, missing keys, Gradio errors, browser/Xvfb failures, or Docker
health and Compose errors. Local document behavior routes to
[document-processing](../document-processing/SKILL.md), and benchmark work
to [gaia-evaluation](../gaia-evaluation/SKILL.md).
