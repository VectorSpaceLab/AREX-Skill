# Troubleshooting Development and CI Failures

Use this reference when a TorchRL edit appears correct locally but fails, skips unexpectedly, or is missing maintainer coverage.

## CUDA tests silently never run

Symptom:

- A CUDA-only test is decorated with a CUDA skip condition, but it is absent from GPU CI results.
- CPU CI reports it skipped or did not run, and GPU CI deselects it.

Likely cause:

- The test has `pytest.mark.skipif(not torch.cuda.is_available(), ...)`, `not torch.cuda.device_count()`, `_has_cuda`, `_has_triton`, or equivalent CUDA/Triton-only gating without `pytest.mark.gpu`.
- CPU jobs use `-m 'not gpu'`; GPU jobs use `-m gpu`. Missing the marker can make the test invisible to both sides.

Fix:

1. Add `pytest.mark.gpu` at function, class, or module scope.
2. Keep the CUDA skip condition so local CPU execution still skips safely.
3. Do not add `pytest.mark.gpu` to tests that intentionally exercise CPU and GPU through fallback parametrization.
4. Run the bundled checker:

```bash
# From the development-and-testing sub-skill directory:
python scripts/check_gpu_marker_policy.py changed_test.py
```

## Optional-dependency suite did not run

Symptom:

- A PR changes Gym/Gymnasium, simulator, Ray, rendering, LLM/VLA, dataset, or other optional integration code, but CI only checked imports.

Likely cause:

- The PR lacks `ci/optdeps`, so the default pull-request path uses the optional-dependencies smoke rather than the full long suite.

Fix:

1. Add `ci/optdeps` when optional integrations or import paths change.
2. Apply the label before pushing a commit or rerunning workflows; labels alone do not retrigger CI.
3. Keep optional imports guarded so base TorchRL remains importable without extras.
4. Document which optional dependency or backend remains unverified locally.

## Old dependency compatibility missed

Symptom:

- Code passes on current torch but fails on the oldest supported stable stack.

Likely cause:

- A new torch API, keyword argument, behavior flag, or dependency assumption was introduced without running the olddeps suite.

Fix:

1. Add `ci/olddeps` when using a torch API that may be newer than the oldest supported stack.
2. Prefer compatibility helpers such as `torchrl.implement_for` for version dispatch.
3. Avoid string-based `torch.__version__` branches.
4. Add tests that exercise the old and new behavior boundary if practical.

## New public API missing docs/reference entry

Symptom:

- Public class/function exists and has tests, but docs or review flag missing API reference coverage.

Likely cause:

- The relevant `docs/source/reference/*.rst` file was not updated, or docstrings lack required sections/examples.

Fix:

1. Add the public object to the right reference file by API family.
2. Ensure the docstring documents args and returns and includes a runnable `>>>` example when practical.
3. For paper-backed features, include a short citation and arXiv link in the class docstring.
4. Use repository doc checker scripts if available in the working checkout.

## Hydra config mismatch

Symptom:

- Direct constructor usage works, but Hydra instantiation or config tests fail.
- A new kwarg is ignored by configs or has a different default.

Likely cause:

- A class with a `*Config` companion under `torchrl/trainers/algorithms/configs/` changed without config parity.

Fix:

1. Add the kwarg to the matching config dataclass with the same default.
2. Update the `_make_*` factory to pop/transform/forward the kwarg.
3. Update cross-references in both class and config docstrings.
4. Extend `test/test_configs.py` or the area-specific config test.
5. Check `Literal[...]` options and `NestedKey` support match the runtime class.

Difficult case to watch: a loss or trainer accepts a new `__init__` kwarg and direct tests pass, but Hydra users cannot set it because the config dataclass and factory were not updated.

## Function-level import anti-pattern

Symptom:

- Review rejects a helper because it imports inside a function or method.

Likely cause:

- Import placement violates TorchRL agent contribution rules.

Fix:

1. Move ordinary imports to module top.
2. For optional dependencies, add a module-top availability probe such as `_has_package = importlib.util.find_spec("package") is not None` and lazily import only behind that gate when necessary.
3. For circular imports, try `TYPE_CHECKING` and type-only imports first.
4. Cache lazy optional imports on the owning object if repeated use matters.

## `print()` or `time.time()` added to library code

Symptom:

- Lint/review flags debugging output or ad-hoc timing.

Fix:

- Replace library `print()` calls with the TorchRL logger surface.
- Replace timing blocks with `torchrl.timeit`.
- In tutorials, prefer prose comments and structured narrative rather than explanatory printing.

## TensorDict key or type-hint review failures

Symptom:

- API works for a flat key but fails with nested keys, or reviewers request more specific typing.

Fix:

1. Type TensorDict keys as `NestedKey` where applicable.
2. Add nested-key tests.
3. Use `Literal[...]` for fixed string modes.
4. For objectives, expose key customization through `_AcceptedKeys` and `set_keys()`.
5. Keep docs and examples aligned with accepted key names.

## `torch.compile` or cudagraph regression

Symptom:

- A hot path passes eager tests but fails under compile or graph capture.

Likely causes:

- Python branching on tensor values;
- data-dependent shapes;
- `.item()` in a repeated path;
- dtype/device instability;
- hidden CPU/GPU transfer;
- mutation patterns incompatible with capture.

Fix:

1. Prefer tensor masks and `torch.where(...)` over Python control flow on tensor values.
2. Avoid dynamic allocation or shape changes in repeated hot paths.
3. Keep devices and dtypes stable.
4. Add focused compile tests where reasonable.
5. For GPU-only capture claims, verify on a provisioned GPU stack before marking the backend verified.

## Process-spawning and xdist flakes

Symptom:

- Tests pass locally but fail under CI sharding or xdist.

Likely cause:

- Collectors, parallel envs, services, inference servers, loggers, and similar tests spawn processes or services and may be quarantined into serial shards.

Fix:

1. Reproduce with the closest file-level shard rather than full parallel pytest.
2. Keep process lifecycle cleanup explicit.
3. Avoid global state that leaks across tests.
4. Use focused serial runs for process-spawning tests before expanding coverage.

## Docs tooling mismatch

Symptom:

- Docs build or docs check fails after text-only changes.

Fix:

1. Check RST heading underline lengths when editing reference docs.
2. Check public docstring argument lists after changing signatures.
3. Keep Sphinx cross-references consistent with existing nearby files.
4. Do not add broken links to original source paths from runtime skill Markdown; source paths are evidence, not runtime documentation links.
