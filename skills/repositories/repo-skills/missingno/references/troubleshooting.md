# missingno Troubleshooting

## When to read

Read this when package import, plotting, optional docs, smoke checks, or
maintainer-test setup behaves unexpectedly. Plot-specific details live in
[sub-skills/visualizations/references/troubleshooting.md](../sub-skills/visualizations/references/troubleshooting.md);
filter/sort details live in
[sub-skills/nullity-utilities/references/troubleshooting.md](../sub-skills/nullity-utilities/references/troubleshooting.md).

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'missingno'` | Package not installed in the active Python environment | Install with `python -m pip install missingno`, then run `python -c "import missingno as msno; print(msno.__version__)"`. Use the same `python` that will run the analysis notebook/script. |
| `ModuleNotFoundError` for `numpy`, `matplotlib`, `scipy`, `seaborn`, or `pandas` | Runtime dependencies are missing or the wrong environment is active | Reinstall `missingno` in the target environment. `seaborn` brings pandas in modern installs, but a broken environment may still need repair. Run `python -m pip check` after installation. |
| Import works in a repo checkout but not elsewhere | The checkout path, not the installed package, was on `sys.path` | Verify from a neutral directory with `python -c "import missingno, inspect; print(missingno.__version__)"` and install the package into the target environment. |
| `AttributeError: module 'missingno' has no attribute 'geoplot'` | Older documentation text mentions `geoplot`, but this snapshot exports only matrix/bar/heatmap/dendrogram and utilities | Do not route users to `geoplot` for this snapshot. Use the verified exports in the root `SKILL.md`. |
| `TypeError: ... got an unexpected keyword argument 'inline'` | Older configuration text mentions an `inline` keyword that is not in the verified signatures for this snapshot | Remove `inline=`. Plot functions return matplotlib `Axes`; save or customize the returned figure/axes directly. |

## Headless plotting and notebooks

Use a non-interactive backend in CI, servers, or agent tools:

```bash
MPLBACKEND=Agg python scripts/missingno_smoke_check.py --plot all --output-dir /tmp/missingno-smoke
```

If a script hangs or errors while trying to display a plot, set
`MPLBACKEND=Agg` before importing matplotlib or configure `matplotlib.use("Agg")`
at the top of the script. Close figures after saving to avoid memory growth in
batch checks.

## No package CLI

`setup.py` does not define console entry points, and package inspection did not
verify a `missingno` command. Use Python APIs instead:

```python
import missingno as msno
ax = msno.matrix(df, sparkline=False)
ax.figure.savefig("missingness-matrix.png", bbox_inches="tight")
```

## Network sample data

The public README demonstrates a remote CSV. That dataset is useful for a
quickstart, but smoke checks and generated examples should avoid network access.
Use the bundled synthetic-data helper instead:

```bash
python scripts/missingno_smoke_check.py --skip-plots
```

## Dependency and version notes

- This snapshot is `missingno` 0.5.2.
- Public runtime dependencies from metadata are `numpy`, `matplotlib`, `scipy`,
  and `seaborn`; pandas is required by the APIs and is installed through the
  plotting stack in current environments.
- Test extras install `pytest` and `pytest-mpl`; they are for repository tests,
  not ordinary package use.
- No GPU, CUDA, ROCm, MPS, credentials, external services, or model/data caches
  are required for selected workflows.

## When to stop and refresh

Run `refresh-repo-skill` instead of patching around the issue if:

- The installed `missingno.__version__` or public function signatures differ
  from this skill.
- A future checkout adds/removes public plotting APIs, especially `geoplot` or
  an `inline` option.
- Root docs, setup metadata, or tests have changed in ways that affect public
  usage.
