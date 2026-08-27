# Contributor guidance for RLinf extensions

Use this reference for coding, config, logging, test, documentation, commit, and PR expectations that apply across extension kinds.

## Code style

- Follow Google Python style for public APIs, classes, functions, and docstrings.
- Add type hints to public functions and methods. Include return types when static inference is unclear.
- Keep local style consistent with nearby code: naming, helper placement, error messages, metric keys, and class organization.
- Prefer small factories/registries over broad conditional patches when an extension will grow.
- Keep errors actionable: invalid configs and unsupported backends should name the bad value and the supported values or required fix.

## Ruff and formatting

RLinf uses Ruff for lint and format with a line length of 88, Python 3.11 target, first-party import sorting for `rlinf`, double quotes, and Google pydocstyle convention. Before handoff, format and lint the changed files if the environment permits.

Common lint-sensitive points for extensions:

- Avoid unused imports introduced only for registration side effects unless explicitly marked with `# noqa: F401` and justified.
- Add docstrings to public classes/methods when the module is in a docstring-enforced area.
- Keep imports sorted and avoid broad `except Exception` unless the code logs and handles a concrete recovery path.
- Do not hide unsupported cases behind `assert False` in new user-facing code; prefer `ValueError`, `NotImplementedError`, or `AssertionError` with clear messages depending on existing local style.

## Logging and diagnostics

- Inside `Worker` subclasses, use `self.log_info(...)`, `self.log_warning(...)`, and `self.log_error(...)`.
- Outside workers, use RLinf logging helpers or Python logging.
- Avoid production `print(...)` in new code. If adapting code near existing prints, do not expand print-based diagnostics unless the surrounding subsystem intentionally writes console banners.
- Include enough context in logs to identify model type, env type, worker rank, backend, or config mode without leaking credentials.

## Configuration YAML rules

- YAML values should be static. Do not perform arithmetic or dynamic computation in YAML.
- Do not overwrite user-facing config fields in code after validation except for explicit derived defaults already owned by validation.
- Copy existing config structure for the nearest task/backend instead of inventing a new layout.
- If an extension adds a field, document it and validate it. Prefer early config failures over remote worker crashes.
- Keep config names consistent across examples, e2e configs, docs, and CI job names.

## Tests and docs requirement

All user-facing changes need tests and documentation.

Recommended layering:

1. Unit tests for pure registries, validation, parsing, tensor math, and small factories.
2. Worker/runner wiring tests where CPU-safe; skip accelerator-only cases with specific reasons.
3. E2E tests for public model/env/task workflows using the smallest feasible config.
4. Documentation that covers install, quick start, configuration, expected behavior, and limitations.

If a full e2e requires GPUs, simulators, assets, physical hardware, or proprietary endpoints, still add the narrowest possible non-mutating or skipped test plus explicit docs on prerequisites.

## Distributed extension hygiene

- Registration code that only runs in the driver is not enough for Ray workers.
- External packages should centralize registrations in an importable `register()` function and set `RLINF_EXT_MODULE`.
- Keep registration idempotent where possible. Use `force=True` only when intentionally overriding an existing model registration with a compatible implementation.
- Do not rely on interactive notebooks or driver-local monkey patches for production runs.

## Commit and PR rules

- Use Conventional Commits: `<type>(<scope>): <description>`.
- Keep commit/PR descriptions imperative and concise.
- Every commit needs a `Signed-off-by:` line; use `git commit -s`.
- PR titles follow commit style and are stricter: lowercase imperative description, ASCII, limited description length, and valid scope characters.
- PR descriptions should include what changed, motivation/context, how it was tested, docs status, and any performance/stability concerns.
- For performance-sensitive changes, include concrete test results and note hardware/backend.

## Review handoff checklist

For any extension handoff, include:

- Extension kind, selected mode (external vs core), and user-facing scope.
- Source touchpoints changed.
- Config fields added/changed and validation behavior.
- Tests run and tests intentionally skipped.
- Docs/README/CI/install/Docker status.
- Known unsupported platforms/backends and the user-visible failure message.
- Any TODOs that remain, tagged clearly for future agents/contributors.
