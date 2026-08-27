# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `NotImplementedError: VJP of ... not defined` | The primitive was registered without a VJP for the argnum you are differentiating, or the `argnums` list is wrong. | Register the staged VJP rule or narrow the differentiation target. |
| `NotImplementedError: JVP of ... not defined` | The primitive was registered without a JVP for the argnum you are differentiating, or the `argnums` list is wrong. | Register the staged JVP rule or run only reverse-mode checks. |
| `TypeError: Bad VJP` / `TypeError: Bad JVP` | The maker returned the wrong object, or the staged closure has the wrong signature. | Make sure the maker returns a closure and that the closure consumes the right staged inputs. |
| Higher-order `check_grads` failure | The closure body uses non-differentiable operations, stale values, or an unsupported backend pattern. | Rewrite the closure in terms of Autograd primitives and keep the staged body differentiable. |
| Deprecated wrapper warnings | The code is still using `.defvjp`, `.defgrad`, `.defvjp_is_zero`, or `quick_grad_check`. | Keep the warning for compatibility, but migrate the implementation to `autograd.extend`. |
| `check_grads` only fails for some arg/kwarg combinations | A shared-cache rule or a missing argnum is only covered in some paths. | Use `defvjp_argnums` / `defjvp_argnums` and verify the Cartesian product with `combo_check`. |

## Quick reminders

- If an argnum is intentionally omitted, `NotImplementedError` is the expected failure.
- For zero tangents or covectors, prefer `vspace(...).zeros()` so the container type matches.
- New code should import `primitive` from `autograd.extend`, not from the legacy compatibility path.
