# Repository provenance

- schema: `disco.repo-provenance.v1`
- package: `sunpy`
- public project: SunPy core package (Python for Solar Physics)
- source commit: `d2ae0740e520f513fa8b91a4b8f82906c2599d80`
- branch: `main`
- exact tag: none at the source commit
- source checkout state: clean at extraction time
- package version observed from metadata/installed inspection: `0.1.dev1+gd2ae0740e`
- Python requirement in source metadata: `>=3.12`
- remote URL: omitted from this provenance record; the package identity and public project name are sufficient for refresh routing

## Relative evidence baseline

- `pyproject.toml` — distribution metadata, base dependencies, extras, ASDF entry points
- `README.rst` — project purpose and high-level installation/use intent
- `sunpy/__init__.py` — public package metadata, logger, config, diagnostics
- `sunpy/coordinates/`, `sunpy/time/` — frames, transforms, ephemerides, time parsing/ranges
- `sunpy/map/`, `sunpy/image/`, `sunpy/visualization/` — Map/WCS, image, and plotting APIs
- `sunpy/net/`, `sunpy/io/` — Fido/provider clients and local file readers
- `sunpy/timeseries/`, `sunpy/sun/`, `sunpy/physics/` — time series, constants/models, and differential rotation
- `docs/tutorial/`, `docs/how_to/`, `docs/topic_guide/`, `docs/reference/` — user workflow and troubleshooting intent
- `examples/` — representative user recipes, classified for safe adaptation or documentation-only handling
- `sunpy/**/tests/` and `sunpy/data/test/` — behavior evidence and local fixtures used to select deferred verification cases

This runtime skill distills the evidence into its own references and scripts.
It does not require the original checkout to remain available. Refresh the skill
when public APIs, extras, supported Python versions, provider clients, file
formats, or workflow behavior change materially.
