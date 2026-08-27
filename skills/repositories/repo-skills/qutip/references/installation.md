# Installation and import checks

QuTiP is a scientific Python package with compiled extensions and optional plotting/runtime extras.

## Recommended install patterns

Minimal runtime install:

```bash
python -m pip install qutip
```

Common interactive and plotting-friendly install:

```bash
python -m pip install "qutip[graphics,runtime_compilation,extras]"
```

The extras used most often in QuTiP workflows are:

- `graphics` for Matplotlib-based visualization helpers.
- `runtime_compilation` for time-dependent string coefficients compiled with Cython.
- `extras` for `loky`, `tqdm`, and `mpmath`.

## What the package expects

- Python 3.11 or newer.
- NumPy and SciPy already installed.
- `matplotlib` if you plan to use Bloch, Hinton, Wigner, or other plotting helpers.
- `cython` and `filelock` if you use string-based time-dependent coefficients.

## Minimal checks

After installing, verify the package identity:

```bash
python -c "import qutip; print(qutip.__version__)"
```

For a richer summary of versions and environment details, use:

```bash
python -c "import qutip; qutip.about()"
```

If `qutip.about()` or a solver behaves strangely, inspect `qutip.settings` in the same interpreter that imported QuTiP.

## Common install notes

- If `import qutip` fails from inside a source checkout, make sure you installed the package into the active environment rather than relying on the repository tree.
- If time-dependent coefficients fail to compile, check that `cython`, `setuptools`, `wheel`, and `filelock` are installed.
- If plotting helpers fail, confirm that Matplotlib is installed and a non-interactive backend is available in headless environments.
