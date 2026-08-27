# Installation

## Purpose

Read this when you need to install Autograd for use with this skill or when you want the shortest reproducible smoke path.

## Supported public installs

Base package:

```bash
pip install autograd
```

With SciPy wrapper coverage:

```bash
pip install "autograd[scipy]"
```

Editable install from a local checkout:

```bash
pip install -e '.[scipy]'
```

Optional interoperability extras:

```bash
pip install xarray
```

## Verified runtime facts

- Autograd is a Python library for differentiating NumPy code.
- The package metadata requires Python `>=3.10` and depends on `numpy<3`.
- `autograd.scipy` is an optional surface that needs SciPy installed.
- `xarray` is not required for the core package; it is only used for container-interoperability examples and tests.

## Recommended smoke order

1. Install the package.
2. Run `python scripts/autograd_smoke.py`.
3. If you need the SciPy surface, rerun with `--require-scipy`.
4. If you need the xarray route, move to `sub-skills/numpy-scipy-primitives/SKILL.md` and its smoke helper after installing xarray.

## When an install looks wrong

- If `import autograd` fails, confirm you are using the environment that contains the install.
- If `autograd.scipy` fails to import, install SciPy or `autograd[scipy]`.
- If `pip check` reports conflicts, repair the environment before trusting any smoke result.
