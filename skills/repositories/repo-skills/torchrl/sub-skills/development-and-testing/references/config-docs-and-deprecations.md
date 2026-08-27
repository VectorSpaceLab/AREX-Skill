# Config, Docs, and Deprecations

Use this reference when a TorchRL edit changes public APIs, constructors, Hydra-configurable components, tutorials, benchmarks, SOTA scripts, or compatibility behavior.

## Public API documentation gate

For every new public class or function:

1. Add or update the public docstring with accurate arguments, returns, and at least one runnable `>>>` example when practical.
2. Add the public object to the relevant file under `docs/source/reference/*.rst`.
3. If the API belongs to a major feature family, update the nearest tutorial or add one under `tutorials/`.
4. If the API is paper-backed, include an arXiv link and a short citation in the class docstring.
5. Keep examples dependency-light where possible; isolate optional dependencies behind clear gates.

Reference docs are organized by API family. Common destinations include environment, transform, collector, replay-buffer, module, objective, trainer, LLM, VLA, service, render, and utility reference files.

## Tutorial gate

Add or extend a tutorial for headline features such as a new algorithm family, collector topology, environment wrapper, or major workflow. Tutorials should be Sphinx-first:

- use prose comments for explanation rather than explanatory `print(...)` calls;
- include sections equivalent to what the user will learn, conclusion, and further reading;
- prefer deterministic short-running examples over long training loops;
- clearly mark optional simulator, rendering, model download, or hardware requirements.

## Benchmark gate

For performance-relevant changes, add or extend a benchmark under `benchmarks/`. This applies especially to collectors, replay buffers, storages/samplers, losses, transforms, environment stepping, recurrent modules, LLM/VLA preprocessing, and other hot paths.

Correctness-only bug fixes do not require a benchmark unless they affect a performance-sensitive path or change expected scaling.

## SOTA gate

A new algorithm needs more than unit tests:

- a runnable script under `sota-implementations/<algo>/`;
- a Hydra config for the script;
- entries in `sota-check/`;
- inclusion in the SOTA smoke test list used by Linux SOTA CI.

Keep long training launchers reference-only for ordinary development tasks; use small unit tests to validate wiring and reserve SOTA execution for the appropriate CI or requested benchmark run.

## Hydra config/class parity

Some TorchRL classes, including trainers, losses, replay-buffer components, transforms, and related building blocks, have Hydra `*Config` dataclass companions under `torchrl/trainers/algorithms/configs/`.

When adding or changing a constructor kwarg on a class with a config companion:

1. Find the matching `*Config` dataclass.
2. Add the kwarg as a config field with the same default and compatible type.
3. Update the matching `_make_*` factory so the field is popped, transformed if needed, and forwarded to the real constructor.
4. Preserve `_target_` patterns and existing dataclass conventions.
5. Add or update `test/test_configs.py` coverage for Hydra instantiation and changed defaults.
6. Update both cross-references:
   - Config docstring: `Hydra configuration for :class:`...``
   - Class docstring: `See also :class:`...Config``

Adding a constructor kwarg without config parity silently breaks Hydra users. Treat this as a release-blocking mismatch for maintainer tasks.

### Parity review checklist

For every changed public constructor in a config-covered area, compare:

- class `__init__` parameters;
- `*Config` dataclass fields;
- default values;
- allowed `Literal[...]` choices;
- NestedKey handling;
- factory `_make_*` argument popping and forwarding;
- docs and examples;
- test coverage.

## Deprecations and backwards compatibility

TorchRL expects two minor releases of warning before breaking changes.

If the next release is `0.X`:

- deprecate in `0.X`;
- change defaults in `0.(X+1)` when appropriate;
- remove in `0.(X+2)`.

Use:

- `DeprecationWarning` for API removals;
- `FutureWarning` for upcoming default changes.

Always name the target version explicitly in warning text, for example:

```python
"MyClass.foo is deprecated and will be removed in v0.X+2. Use MyClass.bar."
```

Add tests that assert the warning category and message, and update docs so users know the replacement path.

## Optional dependency and docs interactions

If a public API exposes an optional backend:

- keep imports safe with module-top availability probes;
- keep import paths working even when the optional package is absent;
- add `ci/optdeps` when integration paths or optional import behavior changed;
- document which functionality requires the optional dependency;
- avoid claiming CPU verification proves backend-specific behavior.

## Documentation checker scripts

The repository contains contributor tools for docstring argument and Sphinx underline checks. They are intentionally not bundled into this runtime sub-skill because they are project maintenance scripts. If the future agent has a checkout and wants those exact checks, use the repository's own tools from the source tree.

This sub-skill bundles only deterministic helpers for test selection and GPU-marker policy.
