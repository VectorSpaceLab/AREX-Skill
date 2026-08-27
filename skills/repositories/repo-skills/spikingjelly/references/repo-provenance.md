# Repo Provenance

- Source project: SpikingJelly
- Source commit: `4db45330bfd283c6cd4bb76b3d62ddc416539cf5`
- Source branch: `master`
- Package version from source: `2.0.0.dev1`
- Generated skill id: `spikingjelly`
- Generated skill root: `skills/disco/spikingjelly/`
- Inspection environment: isolated private Python environment; its local path is intentionally not published
- Verification target: install/import inspection, safe smoke scripts, and deferred native candidate maps

## Evidence paths

- `README.md`
- `CHANGELOG.md`
- `pyproject.toml`
- `requirements.txt`
- `docs/source/tutorials/en/`
- `docs/source/APIs/`
- `test/`
- `skills/tests/spikingjelly/reports/environment/repo_env_report.json`
- `skills/tests/spikingjelly/reports/integration/`

## Notes

The source checkout was used as evidence only. Runtime instructions in the generated skill should rely on the installed package and the bundled sub-skill references/scripts rather than on the checkout staying available.
