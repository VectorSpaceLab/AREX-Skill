---
name: autograd
description: "Routes Autograd install, differentiation, wrapper, extension, and
  optimization workflows for NumPy-based scientific Python code."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Autograd

Use this repo skill when a user asks about Autograd gradients, Jacobians, Hessians, custom primitives, `autograd.numpy`, `autograd.scipy`, structured optimizers, or fixed-point helpers. The package is library-only; there is no CLI route.

## Read first

- `references/installation.md` for public install commands and optional extras.
- `references/repo-provenance.md` when checking whether this skill matches the current repository state or before refreshing it.
- `references/troubleshooting.md` for cross-cutting install, import, optional-dependency, and usage failures.
- `scripts/autograd_smoke.py` for a quick install-and-import sanity check.

## Route map

- **Core differentiation**: [sub-skills/differentiation-core/SKILL.md](sub-skills/differentiation-core/SKILL.md)
  - Use for `grad`, `jacobian`, `elementwise_grad`, `value_and_grad`, higher-order derivatives, `make_vjp`, `make_jvp`, `holomorphic_grad`, and gradient checking.
- **NumPy and SciPy wrappers**: [sub-skills/numpy-scipy-primitives/SKILL.md](sub-skills/numpy-scipy-primitives/SKILL.md)
  - Use for `autograd.numpy`, `autograd.scipy`, supported/unsupported NumPy patterns, xarray interoperability, and missing SciPy-extra troubleshooting.
- **Custom primitives**: [sub-skills/extend-primitives/SKILL.md](sub-skills/extend-primitives/SKILL.md)
  - Use for `primitive`, `defvjp`, `defjvp`, deprecated wrapper compatibility, and gradient checking around a new rule.
- **Optimization workflows**: [sub-skills/optimization-workflows/SKILL.md](sub-skills/optimization-workflows/SKILL.md)
  - Use for `flatten`, structured optimizers, `fixed_point`, and `scipy.optimize.minimize` with `value_and_grad`.

## Install

For a regular user install:

```bash
pip install autograd
```

For the full NumPy/SciPy wrapper surface used by this skill:

```bash
pip install "autograd[scipy]"
```

If you are working from a checkout and want an editable install:

```bash
pip install -e '.[scipy]'
```

Optional xarray container-interoperability examples need `xarray` installed separately.

## Minimal smoke

Run the bundled smoke helper after installation:

```bash
python scripts/autograd_smoke.py
```

Use `--require-scipy` when you want the smoke to fail instead of skipping the optional SciPy section.

## How to choose a route

- If the problem is “what derivative operator should I use?”, start with **differentiation-core**.
- If the problem is “why does a NumPy/SciPy expression fail or behave oddly under Autograd?”, start with **numpy-scipy-primitives**.
- If the problem is “how do I make my own function differentiable?”, start with **extend-primitives**.
- If the problem is “how do I optimize a structured parameter tree or use SciPy minimize?”, start with **optimization-workflows**.

## Notes for future refreshes

Read `references/repo-provenance.md` before refreshing this skill against a new Autograd checkout. The provenance snapshot records the source commit, dirty state, package version, and evidence paths used to build the current skill.
