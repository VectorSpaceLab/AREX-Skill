---
name: deployment-extensions
description: "Use GluonTS CLI checks, shell train/serve deployment contracts,
  inference payload validation, and optional extension adapters."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# deployment-extensions

Use this sub-skill when a task involves package CLI/version checks, `gluonts.shell` training or serving entrypoints, SageMaker-style inference payloads, batch transform JSON Lines, dynamic shell forecaster selection, or optional `gluonts.ext` adapters.

## Route by task

- **Package sanity/version checks:** read `references/cli-reference.md` and run `python -m gluonts version` in the target environment.
- **Shell train/serve contract:** read `references/deployment-workflows.md` before using `python -m gluonts.shell train` or `python -m gluonts.shell serve`.
- **Inference payload shape:** run `scripts/shell_payload_validator.py --help`, then validate a request JSON before sending it to a GluonTS shell endpoint.
- **Batch transform JSON Lines:** read `references/deployment-workflows.md#batch-transform-json-lines`; the bundled validator checks normal JSON request envelopes, while batch mode supplies configuration through `INFERENCE_CONFIG`.
- **Optional adapters:** read `references/extension-adapters.md` before importing `gluonts.ext.*`; most adapters require optional Python packages, R packages, or service dependencies.
- **Failures:** read `references/troubleshooting.md` for missing extras, forecaster lookup, nested hyperparameters, static/dynamic serving confusion, and legacy backend caveats.

## Safe local checks

These commands perform no Docker build, web-server startup, AWS call, training, or checkout-relative read:

```bash
python -m gluonts --help
python -m gluonts version
python -m gluonts.shell --help
python path/to/scripts/shell_payload_validator.py --help
python path/to/scripts/shell_payload_validator.py --input request.json
```

`gluonts.shell` help requires the shell dependencies (`flask` and `waitress`) to be installed. For deployment containers, install the package with the `shell` extra plus any model-specific extras needed by the selected forecaster.

## Boundaries

This sub-skill covers deployment interfaces and extension routing only. It does not build Docker images, start production servers, call AWS APIs, install untrusted dynamic code, or verify optional extension backends by default. MXNet workflows are legacy and were not selected as verified required workflows; do not claim MXNet deployment support unless the user supplies and verifies a compatible environment.
