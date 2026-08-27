---
name: installation-and-backends
description: "Routes PhiFlow installation, import, backend detection, and
  environment smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Installation and Backends

Use this sub-skill when the user asks to install PhiFlow, verify that the
package imports, check `phi.verify()`, inspect `phi.detect_backends()`, or sort
out missing optional backend/UI dependencies.

## Route here for

- editable installs from a local checkout
- published-package installs via `pip install phiflow`
- import failures involving `phi` or `phiml`
- backend detection and backend readiness questions
- Dash / Plotly web-UI setup and smoke checks

## Do not route here

- field, geometry, scene, or mesh workflows -> `core-data-and-geometry`
- advection, diffusion, fluids, waves, FLIP, or SPH -> `physics-and-simulation`
- gradients, Jacobians, or inverse problems -> `optimization-and-learning`
- plotting, controls, or scalar logs after install -> `visualization-and-ui`

## Start with these commands

```bash
python -m pip install -e .
python scripts/check_install.py --show-backends
```

If you only need the published wheel, install `phiflow` from PyPI. The import
name is `phi`, and the repository depends on `phiml` for the tensor/backends
layer.

## Verified runtime facts

- `phi.verify()` is the package smoke check and reports the minimal runtime
  status plus the Dash / Plotly web-UI status.
- `phi.detect_backends()` returns the registered backends that are available in
  the current environment.
- `phi.flow` re-exports the common field, geometry, physics, and plotting names
  for convenience, but this sub-skill still expects the package to be installed
  correctly.

## Common choices

1. **Local inspection from a checkout:** use editable install plus the smoke
   script in this skill tree.
2. **Only need the published package:** install `phiflow`, then run
   `python -c "import phi; phi.verify()"`.
3. **Need web UI support:** install `dash` and `plotly` as well.
4. **Need backend-specific work:** install the backend wheel that matches the
   workflow you are actually using, then re-run the smoke check.

## Read next

- [`references/install-and-backends.md`](references/install-and-backends.md)
  for install choices and backend notes.
- [`references/troubleshooting.md`](references/troubleshooting.md) for missing
  package, missing backend, or stale-doc failures.
- [`../../scripts/check_install.py`](../../scripts/check_install.py) to run the
  safe install smoke check from this skill tree.
