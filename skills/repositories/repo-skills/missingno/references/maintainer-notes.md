# Maintainer Notes

## When to read

Read this only when the task is to edit, test, or review the upstream
`missingno` repository. For ordinary package use, start from the root router and
sub-skills instead.

## Package shape

- Distribution name: `missingno`.
- Import name: `missingno`.
- Public source package: `missingno/`.
- Public exports in this snapshot: `matrix`, `bar`, `heatmap`, `dendrogram`,
  `nullity_filter`, `nullity_sort`, and `__version__`.
- Runtime dependencies in package metadata: `numpy`, `matplotlib`, `scipy`, and
  `seaborn`.
- Test extra in package metadata: `pytest` and `pytest-mpl`.

## Focused tests

Utility behavior is covered by ordinary pytest tests and is the safest native
candidate for quick repository checks:

```bash
python -m pip install -e '.[tests]'
python -m pytest tests/test_util.py -q
```

Visualization tests are image-comparison oriented and depend on matplotlib plus
`pytest-mpl`. In headless environments, set an Agg backend:

```bash
MPLBACKEND=Agg python -m pytest tests/test_viz.py -q
```

Treat that command as an upstream-maintainer check, not the safest package smoke
for modern environments. This snapshot's visualization tests can fail under newer
pandas releases because the test fixtures use older offset aliases such as `BQ`
and dtype assignments that newer pandas rejects. If you need to reproduce the
historical test suite exactly, pin a pandas/matplotlib stack compatible with the
repository snapshot or update the tests deliberately.

If image baselines, pytest-mpl behavior, or dependency-version drift make the
full visualization test suite unsuitable, use a native-backed smoke script that
calls the same plotting functions on deterministic synthetic data and asserts
that matplotlib axes are returned. The generated skill bundles one such helper
at [../scripts/missingno_smoke_check.py](../scripts/missingno_smoke_check.py).

## Documentation caveats

- The root README is the principal user documentation.
- `CONFIGURATION.md` contains useful parameter descriptions, but in this
  snapshot it also mentions `inline` and `geoplot` capabilities that were not
  verified in the installed public API. Check signatures before documenting
  these capabilities.
- The README quickstart uses remote sample data; tests do not require that data.
  Avoid making repository tests depend on network downloads.

## Change-review checklist

When editing the repo, keep generated skill staleness in mind:

1. If `missingno/missingno.py` or `missingno/utils.py` changes public
   signatures, update API references and smoke helper expectations.
2. If `setup.py` dependencies or extras change, update install and
   troubleshooting notes.
3. If docs add or remove a public workflow, update root routing metadata and the
   owning sub-skill.
4. If tests add a safer native example or fixture, include it in the native
   candidate map during refresh.
5. If visualization behavior changes under matplotlib, prefer deterministic
   synthetic checks before relying on pixel comparisons in automation.
