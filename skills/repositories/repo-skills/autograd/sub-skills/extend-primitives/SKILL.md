---
name: extend-primitives
description: "Route custom primitive authoring, staged VJP/JVP closures,
  deprecated wrapper compatibility, and gradient checking."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# extend-primitives

Use this sub-skill when a user needs to make a new primitive differentiable or extend an existing primitive with custom reverse- or forward-mode rules.

## Route here for
- `primitive`-based authoring of custom primitives.
- staged `defvjp`, `defjvp`, `defvjp_argnums`, and `defjvp_argnums` closures.
- compatibility work for deprecated `.defvjp`, `.defgrad`, and `.defvjp_is_zero` wrappers.
- gradient checking with `check_grads` and `combo_check`.

## Route elsewhere for
- ordinary differentiation-operator questions, Jacobians, Hessians, and higher-level derivative semantics: [differentiation-core](../differentiation-core/SKILL.md)
- built-in NumPy/SciPy wrapper behavior, array protocol behavior, and wrapper limits: [numpy-scipy-primitives](../numpy-scipy-primitives/SKILL.md)

## Evidence anchors
`autograd/extend.py`, `autograd/core.py`, `autograd/test_util.py`, `docs/updateguide.md`, `docs/tutorial.md`, `examples/define_gradient.py`, `tests/test_wrappers.py`

## Bundled runtime files
- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/custom_primitive_smoke.py`

## Operating guidance
1. Start from `autograd.extend.primitive`.
2. Register a staged VJP/JVP rule immediately after the primitive is defined.
3. Use the staged maker to capture only the forward-pass values needed by the derivative.
4. Prefer `defvjp_argnums` / `defjvp_argnums` when one cached calculation should serve several argnums.
5. Use `None` only when a rule is intentionally zeroed; omit the argnum entirely when you want the missing-path `NotImplementedError`.
6. Validate tiny fixtures with `check_grads`; use `combo_check` when several positional or keyword combinations need coverage.
7. Keep deprecated wrapper APIs only for compatibility with existing code and test fixtures; new authoring should use the staged API.

## Quick smoke
Run `python scripts/custom_primitive_smoke.py` before handing off a draft.

## Cross-links
- `differentiation-core` for operator semantics and derivative wrappers.
- `numpy-scipy-primitives` for primitives that wrap ndarray or SciPy behavior.
