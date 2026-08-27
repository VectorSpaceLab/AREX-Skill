---
name: reproducibility-and-capture
description: "Keep Sacred runs reproducible and diagnose runtime capture/settings behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Reproducibility and capture

Use this sub-skill when a Sacred experiment needs deterministic random behavior, reliable source/dependency capture, clean-repository enforcement, stdout/stderr capture control, captured-output filtering, or diagnosis of the global `sacred.SETTINGS` values that affect those behaviors.

## Fast routing

- Read [`references/reproducibility-and-capture.md`](references/reproducibility-and-capture.md) when designing or reviewing seed handling, `_seed`/`_rnd` use, source/dependency discovery, `print_dependencies`, `enforce_clean`, capture modes, logging/capture interactions, settings, or TensorFlow `LogFileWriter` behavior.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when a run is nondeterministic, captures unexpected output, misses sources/dependencies, fails `enforce_clean`, hits `pkg_resources`/setuptools issues, or uses optional TensorFlow capture.
- Run [`scripts/sacred_reproducibility_probe.py`](scripts/sacred_reproducibility_probe.py) after installing Sacred to smoke-test fixed root seeding, deterministic captured-function sub-seeds, and explicit `sys` stdout capture without requiring NumPy or TensorFlow.

## Operating checklist

1. Fix or record the root `seed` before comparing runs. Prefer `Experiment.run(config_updates={"seed": ...})` or CLI `with seed=...`.
2. Put stochastic work inside captured functions that accept `_seed` or `_rnd`; avoid long-lived module-level PRNG state for reproducibility-sensitive paths.
3. Set discovery-related `SETTINGS` before constructing the `Experiment`; set capture options before running it.
4. Use `print_dependencies` to inspect discovered packages, source hashes, and VCS cleanliness before trusting reproducibility metadata.
5. Choose capture mode deliberately: `no` for no stored output, `sys` for Python stream output, `fd` when subprocess/C-level output must be captured on platforms where file-descriptor capture is reliable.
6. Use a captured-output filter for progress bars or very verbose output; use logging levels to keep captured output clean.

## Route elsewhere

- Use the configuration/CLI sub-skill for config-update syntax, named configs, config files, or command registration details beyond the reproducibility use of `seed` and capture flags.
- Use the observers/logging sub-skill for observer storage schemas, database/file observer setup, metrics persistence, artifact/resource storage layouts, and backend-specific observer failures.
