# Contributor Guidance

This reference is for editing TorchRL itself. It distills maintainer rules from `AGENTS.md`, `CONTRIBUTING.md`, `pytest.ini`, CI workflow files, and inspected source layout. Use it after selecting the TorchRL API workflow owner for the feature area.

## What belongs here

Use this guidance for:

- code-style and contribution-policy decisions;
- deciding whether a change needs tests, docs, tutorial, benchmark, SOTA, or CI labels;
- reviewing backend-specific tests and optional dependency behavior;
- maintaining Hydra config/class parity;
- making deprecation and compatibility choices.

Do not use this reference to learn how to construct runtime environments, collectors, policies, losses, or LLM/VLA workflows. Route those API details to the corresponding workflow sub-skill, then return here for maintainer-safe edits.

## File and import rules

For every edited or new Python file:

- Put imports at module top. Do not add function-level imports except for:
  - optional dependencies guarded by a module-top `_has_<name> = importlib.util.find_spec("<name>") is not None` probe, preferably cached if imported lazily later;
  - genuine circular imports, after first trying `typing.TYPE_CHECKING`.
- Do not use wildcard imports.
- New `.py` files start with `from __future__ import annotations`.
- Keep public signatures accurately typed; bad hints are worse than missing hints.
- Prefer `NestedKey` for TensorDict keys unless the value cannot be a TensorDict nested key.
- Use `Literal[...]` for a fixed set of string values rather than a bare `str`.

### Version compatibility

Use `torchrl.implement_for` for torch, gym, gymnasium, or other dependency version dispatch. Do not add hand-rolled branches based on `torch.__version__` or equivalent string comparisons.

Evidence from inspection: `torchrl.implement_for` is exported and importable from the installed package.

## Logging, timing, and visible output

- Do not add `print()` to library code.
- Use `from torchrl._utils import logger as torchrl_logger` or the existing TorchRL logger surface.
- Use `torchrl.timeit` for timing/profiling in project code; do not add ad-hoc `time.time()` timing blocks.
- Tutorial prose may use Sphinx-first comments and narrative, but avoid `print(...)` as explanation.

## TensorDict-first design

New modules, transforms, losses, collectors, replay-buffer components, and public wrappers should accept and return `TensorDict` or `TensorDictBase` rather than parallel dict-like containers.

For objective/loss changes:

- expose TensorDict keys through the existing `_AcceptedKeys` plus `set_keys()` pattern;
- test both flat and nested key forms when `NestedKey` inputs are supported;
- keep key defaults aligned between docs, tests, and examples.

## Compile and cudagraph friendliness

For hot paths such as collectors, replay buffers, losses, transforms, and environment stepping:

- prefer `torch.where(...)`, masks, and tensor operations over Python branches on tensor values;
- avoid data-dependent shapes in repeated execution paths;
- avoid `.item()` on hot paths;
- keep dtype and device stable across calls;
- verify with `torch.compile` when reasonable;
- consider cudagraph assumptions only when devices, shapes, and memory ownership are stable.

Compile/cudagraph verification is strongly encouraged, not a blanket requirement. Treat unsupported optional GPU behavior as unverified unless a backend-specific run actually exercised it.

## Test placement rules

- Every new public class or function needs tests.
- Extend an existing test file when an existing area covers the behavior.
- Create a new test file only when the area is genuinely new; a brand-new objective may use `test/test_<algo>.py`.
- If a test module already has an executable guard, preserve it. If you create a new test file, end with a direct-execution guard that calls `pytest.main(...)`.
- For `NestedKey`-accepting APIs, include a nested-key test, not just a flat string key.

## Public documentation rules

Every new public class or function referenced from the API surface must be represented in `docs/source/reference/*.rst`. Public docstrings should use Sphinx/Google-style sections with `Args:`, `Returns:`, and a runnable `>>>` example when appropriate.

Paper-backed public algorithms/classes should include the arXiv link and a short citation in the class docstring.

No emojis in code, docstrings, comments, commits, or PR text.

## Source-layout conventions to check

Evidence paths used for this sub-skill include:

```text
AGENTS.md
CONTRIBUTING.md
pytest.ini
.github/workflows/test-linux.yml
.github/unittest/
docs/source/reference/*.rst
torchrl/trainers/algorithms/configs/
test/
benchmarks/
sota-check/
```

Use those paths as repository evidence while editing. Do not link runtime Markdown to source docs or scripts; cite them as source paths only.
