# Customization Troubleshooting

Use this reference to diagnose custom ModelScope pipeline/model/preprocessor
scaffolding, registration, configuration, trust-boundary, and contributor-test
failures. Prefer local, deterministic checks before network or GPU/domain runs.

## Scaffold command fails

### `modelscope: command not found`

Cause: the ModelScope CLI is not on `PATH` in the current environment.

Actions:

1. Use the same Python environment where `modelscope` is installed.
2. Try `python -m modelscope.cli.cli --help` only if the checkout supports it;
   otherwise report that the console script is unavailable.
3. Do not install or upgrade packages in a user environment without approval.
4. You can still use `scripts/pipeline_template_plan.py` because it does not
   import ModelScope.

### `the FILENAME must end with .py`

Cause: the scaffold CLI validates `--filename` and rejects non-Python suffixes.

Actions:

- Rename the output file to end with `.py`.
- Use the bundled planner; it performs the same filename check before printing a
  command.

### `template.tpl not exists` or custom template not found

Cause: `--tpl_file_path` is neither a bundled template name nor an existing path.

Actions:

- Use the default `template.tpl` unless a reviewed custom template is required.
- If using a custom template, pass a path that exists in the current working
  context before running the real CLI.
- Review custom templates for top-level writes/imports because their generated
  code will be Python.

### Generated wrapper writes unexpected files

Cause: the stock template includes top-level `Config(...).dump(...)` code. That
code can write `configuration.json` when the generated wrapper is executed, and
may also run if the wrapper is imported as a normal module.

Actions:

- Refactor config writing into an explicit function or an `if __name__ ==
  "__main__":` block.
- Keep registration decorators at import time, but remove downloads, training,
  cache mutations, and file writes from imports.
- Confirm the planned `--configuration_path` is a scratch directory before
  running generated code.

## Registry and pipeline build errors

### `KeyError: <type> is not in the pipelines/models/preprocessors registry group <task>`

Likely causes:

- The custom module was never imported, so decorators did not run.
- `configuration.json` `pipeline.type` or `model.type` does not match the
  decorator `module_name`.
- The task/group key in the decorator does not match the config `task` or the
  `pipeline(task=...)` argument.
- A built-in lazy import index was not regenerated after adding an in-repository
  module that relies on index-driven import.

Actions:

1. Import the custom module explicitly in a smoke test.
2. Inspect `PIPELINES.modules`, `MODELS.modules`, or `PREPROCESSORS.modules` for
   the expected group and alias.
3. Align the config `task`, registry `group_key`, and `module_name` strings.
4. For repository contributions, run the repository's focused builder tests and
   only regenerate package/index artifacts when the contribution workflow calls
   for it.

### Duplicate registration key

Cause: the same `module_name` is already registered in the same registry group
and `force=False`.

Actions:

- Choose a unique alias for the custom component.
- Use `force=True` only in controlled tests where overriding is intentional.
- In plugin packages, avoid common aliases such as `custom-image` unless the
  package owns them.

### Abstract pipeline or missing method errors

Cause: a `Pipeline` subclass did not implement required behavior, or inherited a
method that raises in the selected call path.

Actions:

- Implement deterministic `preprocess`, `forward`, and `postprocess` methods.
- Add `_sanitize_parameters` when user-facing `__call__` keyword arguments need
  to be split among preprocess/forward/postprocess.
- Add `_check_input` and `_check_output` assertions for clearer user errors.
- Test both single input and list/batch input if the pipeline advertises batch
  support.

## Configuration and trust errors

### Python config refused unless `trust_remote_code=True`

Cause: loading an untrusted `.py` config executes Python. ModelScope refuses this
for remote model repositories unless the caller opts in.

Actions:

- Prefer `configuration.json` or YAML for passive configuration.
- If a Python config is truly required, ask the user to verify the source and
  explicitly accept `trust_remote_code=True`.
- Isolate the environment and avoid combining the trust decision with downloads
  or training in the same step.

### Pipeline refuses configs with `plugins` or `allow_remote`

Cause: model configuration can request plugin imports or remote repository code.
ModelScope refuses those when `trust_remote_code=False`.

Actions:

- Explain that plugins and `allow_remote` execute external Python and may install
  or import packages.
- If the user trusts the source, pass `trust_remote_code=True`; otherwise remove
  or avoid those config fields and use local code.
- Do not set `allow_remote` just because the template did. The stock template
  includes `allow_remote: True`; review whether the custom workflow actually
  needs it.

### Plugin module cannot be loaded

Likely causes:

- The plugin package is not installed in the active environment.
- The plugin module name in `.modelscope_plugins` or config is wrong.
- Importing the plugin raises an error from an optional dependency.

Actions:

1. Verify the plugin module import in an isolated Python process.
2. Confirm package name versus import module name.
3. Install missing packages only with user approval and in an isolated
   environment when possible.
4. Keep plugin imports side-effect-light; they should register components, not
   start jobs or mutate user data.

## Contributor check failures

### `make tests` fails but `make test` exists

Contributor guidance may mention `make tests`, while inspected build targets
expose `make test`. Use the target available in the checkout, or run a focused
Python test file directly.

### Missing `data/test/...` fixture

Cause: Git LFS objects or the `data/test` submodule may not be present.

Actions:

- Treat this as an environment/data prerequisite, not automatically as a product
  bug.
- Prefer synthetic fixtures for custom extension tests.
- Do not fetch LFS/submodules without user approval because that may use network
  and disk.

### Optional dependency import errors

Cause: ModelScope covers many domains and optional packages. Customization tests
may import components that need torch, TensorFlow, cv2, decord, audio packages,
Swift, vLLM, or accelerator-specific packages.

Actions:

- Narrow the focused test to the custom code path.
- Skip or mark optional backend checks unless the user has requested that domain
  and the environment has the required packages/hardware.
- Do not claim GPU/CUDA validation from CPU-only imports.

### Linter/pre-commit rewrites broad files

Cause: pre-commit hooks can format or normalize many paths.

Actions:

- During iteration, run hooks on changed files with `--files`.
- Avoid `pre-commit run --all-files` until the user wants a broad repository
  cleanup or final pre-review check.
- Do not commit generated formatting changes unless the user requested commits.

## Quick diagnosis matrix

| Symptom | First safe check | Likely owner |
| --- | --- | --- |
| Scaffold command would write to wrong directory | Run `pipeline_template_plan.py` and inspect `--save_file_path`/`--configuration_path` | CLI planning |
| Pipeline alias not found | Import custom module, then inspect registry modules for group/alias | Registration/config |
| Pipeline asks for `trust_remote_code` | Inspect config for `plugins` or `allow_remote` | Security/trust decision |
| Test fails on missing image/model file | Check whether LFS/submodule data is present | Test data setup |
| GPU-specific test cannot run | Check package/hardware availability and classify optional | Backend environment |
