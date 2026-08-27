# Workflows

## Author a custom primitive

1. Write the pure Python function body.
2. Wrap it with `primitive`.
3. Decide whether the primitive needs reverse mode, forward mode, or both.
4. Register staged rules right away with `defvjp`, `defjvp`, `defvjp_argnums`, or `defjvp_argnums`.
5. If one expensive derivative calculation can serve several argnums, use the `*_argnums` maker form instead of repeating the work.
6. If an argnum should stay unsupported, omit it; `None` means a zero rule, not an unsupported one.
7. Keep the staged closure body differentiable if you need higher-order derivatives.
8. Verify the smallest useful fixture with `check_grads`.
9. If several positional or keyword combinations matter, wrap the check with `combo_check` so the Cartesian product is exercised.

## Migrate old wrapper code

- Legacy `.defvjp`, `.defgrad`, `.defvjp_is_zero`, and `quick_grad_check` calls still exist for compatibility.
- Treat the warnings as a migration signal, not as the preferred authoring path.
- New code should import from `autograd.extend` and use `check_grads` or `combo_check` for validation.

## Smoke route

- Run `scripts/custom_primitive_smoke.py` first.
- Then run one tiny fixture that covers the real primitive's shape, dtype, or kwargs pattern.
- If the rule shares work across argnums, add a fixture that exercises every argnum combination you actually register.

## Later verification cases

Use these synthetic cases when the primitive needs more than the repo's base example:

- Shape-dependent VJP: a primitive whose VJP uses both `ans.shape` and `x.shape`.
- Intentional undefined argnum: a primitive that registers only one argnum and proves the missing-arg failure path.
