# PennyLane development workflows

## Add or modify an operator

1. Identify the owning module under `pennylane/ops/` or `pennylane/templates/`.
2. Use `pennylane.math` for framework-agnostic shape/value checks.
3. For a new operator, implement decomposition/matrix/eigenvalue/adjoint/flatten behavior as appropriate.
4. Validate an instance with:
   ```python
   from pennylane.ops.functions import assert_valid
   assert_valid(op)
   ```
5. Add focused tests under the matching `tests/ops/` or `tests/templates/` path.
6. Run targeted pytest, source/test pylint, black, isort, and `tach check` if imports changed.
7. Add a changelog entry for public user-facing changes.

## Change a device or plugin-related path

1. Identify whether the change is in the base device API, a built-in simulator, or plugin conformance.
2. Add focused tests under `tests/devices/` or the device-specific test path.
3. For plugin compatibility, run `pl-device-test --help` first, then an explicit device command when the plugin is installed.
4. State backend requirements; do not treat CPU `default.qubit` success as plugin/GPU success.

## Change gradient/interface behavior

1. Identify affected framework(s): Autograd, JAX, Torch, TensorFlow legacy, or all interfaces.
2. Mark tests with the proper pytest marker: `autograd`, `jax`, `torch`, `tf`, or `all_interfaces`.
3. Do not hide optional framework absence with `pytest.importorskip` inside unmarked tests.
4. Include scalar and vector-output checks when relevant.

## Change docs or examples

- Use `import pennylane as qp` in examples, docstrings, and tests.
- Run focused docstring/Sybil tests by pointing pytest at the source or doc file when applicable.
- Keep code examples minimal and avoid requiring optional frameworks unless the example is explicitly about them.

## Changelog flow

For user-facing changes, add a bullet under the proper section in `doc/releases/changelog-dev.md` and include a PR-link line of the form:

```text
  [(#XXXX)](https://github.com/PennyLaneAI/pennylane/pull/XXXX)
```

Do not invent a PR number unless the project/user convention for placeholders is clear.

## Module-boundary flow

If imports or module dependencies changed:

1. Inspect `tach.toml` module boundaries.
2. Avoid cross-layer or circular imports.
3. Pay extra attention to `pennylane.labs` and `pennylane.ftqc` restrictions.
4. Run `tach check` repo-wide.

## AI/GitHub content flow

If the user asks for PR/issue/comment text, draft it for review only. Mark AI-generated content that would be posted externally and do not post it yourself.
