# Repo Provenance

- Schema: `disco.repo-provenance.v1`.
- Source package: Astropy core (`astropy`).
- Source repository: `https://github.com/astropy/astropy.git`.
- Source commit: `7556e8eb6c1a80dc694bb30fd87d6773457b037c`.
- Branch at generation time: `main`.
- Exact tag: none detected.
- Package version observed from installed metadata: `0.1.dev1+g7556e8eb6`.
- Python support from package metadata: `>=3.11`.
- Skill generation decision policy: agent-confirmed scope; not imported.
- Working tree state at generation: dirty because generated `skills/` artifacts/logs were present. Source evidence outside `skills/` was not intentionally modified by this skill generation run.

## Evidence Paths Used

Relative source and documentation paths used to build this skill:

- `pyproject.toml`, `setup.py`, `MANIFEST.in`, `tox.ini`, `README.rst`.
- `docs/index.rst`, `docs/index_user_docs.rst`, `docs/install.rst`, `docs/importing_astropy.rst`.
- `docs/units/`, `docs/constants/`, `astropy/units/`, `astropy/constants/`.
- `docs/time/`, `docs/coordinates/`, `astropy/time/`, `astropy/coordinates/`.
- `docs/table/`, `docs/io/`, `astropy/table/`, `astropy/io/`.
- `docs/wcs/`, `docs/nddata/`, `astropy/wcs/`, `astropy/nddata/`.
- `docs/visualization/`, `docs/convolution/`, `astropy/visualization/`, `astropy/convolution/`.
- `docs/modeling/`, `docs/stats/`, `docs/timeseries/`, `docs/uncertainty/`, `astropy/modeling/`, `astropy/stats/`, `astropy/timeseries/`, `astropy/uncertainty/`.
- `docs/cosmology/`, `astropy/cosmology/`.
- `docs/config/`, `docs/utils/iers.rst`, `docs/logging.rst`, `docs/warnings.rst`, `docs/environment_variables.rst`, `docs/samp/`, `astropy/config/`, `astropy/utils/`, `astropy/samp/`.
- Public CLI implementations and console entry points under `astropy/io/fits/scripts/`, `astropy/table/scripts/`, `astropy/visualization/scripts/`, `astropy/io/votable/volint.py`, `astropy/wcs/wcslint.py`, and `astropy/samp/hub_script.py`.

Refresh this skill when Astropy changes public APIs, console entry points, optional dependency groups, FITS/WCS behavior, coordinate/time data behavior, or major documentation routes.
