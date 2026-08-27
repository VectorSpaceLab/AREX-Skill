schema: disco.repo-provenance.v1

# TorchMetrics repo provenance

- Repository: TorchMetrics
- Source commit: `37a808094850aa1e05bc6e9fcf63fae86dfd01ce`
- Branch: `master`
- Exact tag at HEAD: none
- Working tree state: dirty checkout with generated `skills/` output present during skill production
- Package version: `1.9.0`
- Remote URL: omitted-private-or-unknown

## Evidence paths used

All paths below are relative to the repository root.

- `README.md`
- `pyproject.toml`
- `setup.py`
- `requirements/`
- `docs/source/`
- `examples/`
- `src/torchmetrics/`
- `tests/unittests/`
- `tests/integrations/`

## Notes for refresh checks

This skill was distilled from the source tree at the commit above and from a private inspection environment that verified the installed `torchmetrics` package version and basic import behavior.
If the repository or installed package changes, refresh the skill rather than assuming the public guidance is still current.
