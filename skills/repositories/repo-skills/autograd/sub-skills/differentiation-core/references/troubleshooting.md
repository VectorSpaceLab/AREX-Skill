# Troubleshooting

## Purpose

This reference collects the failure modes that most often appear when users ask for scalar/array differentiation, higher-order derivatives, or gradient checking.

## When to read

Read this when a derivative helper raises a `TypeError`, returns a surprising shape, warns about complex inputs, or seems to disagree with finite differences.

## Quick diagnosis table

| Symptom or message | Likely cause | What to do | Next bundled check |
| --- | --- | --- | --- |
| `TypeError: Grad only applies to real scalar-output functions.` | `grad` or `value_and_grad` was used on a vector-valued or complex-valued output | Reduce the function to a real scalar, or switch to `jacobian`, `elementwise_grad`, or `holomorphic_grad` | `references/api-reference.md` and `scripts/differentiation_smoke.py` |
| `TypeError: value_and_grad only applies to real scalar-output functions.` | Same root problem as above, but in the value+gradient helper | Return a real scalar loss first, then compute the gradient | `references/workflows.md` |
| Jacobian/Hessian shape looks transposed or too high-rank | The expected shape was guessed instead of derived from the primal output and input shapes | Remember: `jacobian` returns `output_shape + input_shape`; `hessian` returns `input_shape + input_shape` | `references/api-reference.md` |
| A Hessian-vector or GGN product fails with a shape mismatch | The vector/tensor argument does not live in the same space as the differentiated input | Match the tangent shape to the primal input shape, then compare against an explicit `np.dot` or `np.tensordot` contraction | `references/workflows.md` |
| `Input to holomorphic_grad is not complex` warning | `holomorphic_grad` was called on a real input | Pass a complex input if you want the complex derivative, or use `grad` for a real-valued objective | `references/workflows.md` |
| Gradient checking fails only near a branch or loop threshold | The numerical perturbation changes the executed Python path | Move the test point away from the threshold, lower the sensitivity of the branch, or test the analytic derivative on the chosen branch instead of the boundary | `scripts/differentiation_smoke.py` |
| `checkpoint` gives the same answer but feels slower | This is expected; checkpointing trades recomputation for lower memory use | Use `checkpoint` only when memory is the bottleneck, and keep the original function for speed-sensitive runs | `references/workflows.md` |
| `NotImplementedError: VJP of ... not defined` or `JVP of ... not defined` | A custom primitive is missing a differentiation rule | Route the task to `../extend-primitives/SKILL.md` and stop treating it as a core-operator problem | `../extend-primitives/SKILL.md` |
| `TypeError: Can't differentiate w.r.t. type ...` or `Can't find vector space for value ...` | The selected input type is not one of the core differentiable vector spaces | Convert the leaves to arrays, or if you really need structured tree handling, route to `../optimization-workflows/SKILL.md` | `../optimization-workflows/SKILL.md` |
| `grad_and_aux` returns the wrong auxiliary payload or a zero-looking gradient | The scalar loss was placed in the aux position, or the first output is not the value being differentiated | Ensure the first output is the scalar loss and the second output is the auxiliary payload, even when the aux payload is nested | `references/workflows.md` |

## Recovery checklist

1. Identify whether the failure is about scalar-output constraints, shape confusion, complex numbers, branch sensitivity, or a missing custom rule.
2. Check the operator's return convention in `references/api-reference.md`.
3. Reproduce the smallest possible case in `scripts/differentiation_smoke.py` style.
4. If the failure names a missing primitive rule, stop and hand off to `../extend-primitives/SKILL.md`.
5. If the failure is really about structured parameters or flattening, route to `../optimization-workflows/SKILL.md`.
