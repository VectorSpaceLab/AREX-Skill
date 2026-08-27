# Repo provenance

## Source snapshot

- Repository: Orbit / `orbit-ml`
- Distribution package: `orbit-ml`
- Import package: `orbit`
- Package version: `1.1.5.1`
- Python requirement from package metadata: `>=3.12`
- Source commit: `d1f58a6a9e20764b25ee28773df5355512213dfa`
- Source branch at capture: `dev`
- Source tag at capture: `v1.1.5.1`
- Source dirty state at evidence capture: clean for repository source files
- Generation dirty state: generated skill artifacts live under `skills/`, so the checkout becomes dirty after skill production
- Import status: not imported, per the create request

## Evidence paths used

All paths are relative to the repository root.

- `README.md`
- `CONTRIBUTING.md`
- `pyproject.toml`
- `setup.py`
- `requirements.txt`
- `requirements-test.txt`
- `tox.ini`
- `install_stan.py`
- `orbit/`
- `docs/`
- `examples/`
- `tests/`
- `skills/orbit.log` as a local output-layout signal only

## Generated skill paths

- Runtime skill root: `skills/disco/orbit-ml/`
- Review/test artifact root: `skills/tests/orbit-ml/`

## Staleness checks

Refresh this skill if any of the following change:

- the source commit, tag, or package version differs from the snapshot above
- public constructors or estimator names for `ETS`, `LGT`, `DLT`, `KTR`, or `KTRLite` change
- `orbit.diagnostics.backtest`, `orbit.diagnostics.metrics`, or plotting APIs change
- `orbit.utils.dataset`, `orbit.utils.features`, `orbit.utils.knots`, `orbit.utils.simulation`, or tuning helpers change
- the Stan/CmdStan setup flow or Pyro estimator routing changes
- the direct `orbit.template.ktr` circular-import behavior is fixed or replaced by a new import path
