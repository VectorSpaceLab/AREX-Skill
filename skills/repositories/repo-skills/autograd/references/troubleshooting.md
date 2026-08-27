# Troubleshooting

## Purpose

Use this for package-wide install, import, optional-dependency, and route-selection problems before jumping into a narrower sub-skill.

| Symptom | Likely cause | Next step | Owning route |
| --- | --- | --- | --- |
| `ImportError` for `autograd` | The package is not installed in the current environment, or the wrong Python is active. | Run `python scripts/autograd_smoke.py` from the environment that has the install; if that fails, reinstall Autograd. | root |
| `ImportError` for `autograd.scipy` or `scipy.*` | SciPy is missing from the environment. | Install `pip install "autograd[scipy]"` or `pip install scipy`, then rerun the smoke helper. | `sub-skills/numpy-scipy-primitives/SKILL.md` |
| The user asks for `grad`, `jacobian`, `hessian`, or `value_and_grad` but the failure is a scalar-output or shape issue | The wrong derivative operator was chosen. | Route to `sub-skills/differentiation-core/SKILL.md` and compare the primal input/output shapes. | `sub-skills/differentiation-core/SKILL.md` |
| The error names `primitive`, `defvjp`, `defjvp`, or `check_grads` | A custom rule is missing or the staged closure has the wrong signature. | Route to `sub-skills/extend-primitives/SKILL.md`. | `sub-skills/extend-primitives/SKILL.md` |
| The issue mentions `flatten`, `adam`, `rmsprop`, `sgd`, `fixed_point`, or `scipy.optimize.minimize` | The task is about structured optimization, not a basic derivative operator. | Route to `sub-skills/optimization-workflows/SKILL.md`. | `sub-skills/optimization-workflows/SKILL.md` |
| `A.dot(B)` or in-place mutation behaves oddly under differentiation | The wrapper layer only supports pure `np.dot`/`np.matmul`-style code paths and pure updates. | Rewrite the expression and retry, then use the NumPy/SciPy wrapper route. | `sub-skills/numpy-scipy-primitives/SKILL.md` |
| `xarray` examples fail only because `xarray` is absent | The interoperability example uses an optional dependency. | Install xarray or stay on the base NumPy route. | `sub-skills/numpy-scipy-primitives/SKILL.md` |

## Recovery checklist

1. Verify the active Python matches the environment where Autograd was installed.
2. Run `python scripts/autograd_smoke.py`.
3. If the failure is optional-dependency related, install the missing extra and retry.
4. If the failure is workflow-specific, switch to the sub-skill that owns that workflow instead of forcing the root route.
