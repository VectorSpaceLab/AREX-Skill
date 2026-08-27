# OmicVerse Repo Provenance

- Skill id: `omicverse`
- Source package: `omicverse`
- Source package version: `2.2.4rc1`
- Source repository URL: `https://github.com/omicverse/omicverse.git`
- Source branch: `master`
- Source commit: `77f3a4e6306f0afc88e44093db3fbaeeb248a7dd`
- Exact tag: none recorded at generation time
- Working tree state: dirty because the generated `skills/` artifact tree was added during skill creation; no pre-existing source-code modifications were recorded before generation.

## Evidence Paths

- `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements.txt`, `requirements-latest.txt`, `requirements/`, `conda/`
- `README.md`, `READMEM/`, `docs/`, `readthedocs/`, `omicverse_guide/`, `examples/parametric_umap_projection.md`
- `omicverse/__init__.py`, `omicverse/cli.py`, `omicverse/_registry.py`, `omicverse/_optional.py`, `omicverse/_settings.py`
- `omicverse/io/`, `omicverse/datasets/`, `omicverse/pp/`, `omicverse/pl/`, `omicverse/report/`, `omicverse/utils/`
- `omicverse/single/`, `omicverse/bulk/`, `omicverse/es/`, `omicverse/metabol/`, `omicverse/protein/`, `omicverse/micro/`
- `omicverse/space/`, `omicverse/bulk2single/`, `omicverse/epi/`
- `omicverse/genetics/`, `omicverse/airr/`, `omicverse/mol/`, `omicverse/alignment/`
- `omicverse/mcp/`, `omicverse/jarvis/`, `omicverse/agent/`, `omicverse/llm/`, `omicverse/ov_skill_seeker/`
- `scripts/ci/mcp-report-versions.py`, `scripts/ci/mcp-fast-mock.sh`, `scripts/ci/mcp-core-runtime.sh`, `scripts/ci/mcp-scientific-runtime.sh`, `scripts/ci/mcp-extended-runtime.sh`
- `tests/pp/`, `tests/single/`, `tests/bulk/`, `tests/space/`, `tests/micro/`, `tests/airr/`, `tests/alignment/`, `tests/mcp/`, `tests/jarvis/`, `tests/utils/`, and representative root tests named in integration artifacts.

## Inspection Summary

The skill was generated from repository evidence plus a private isolated inspection environment that verified package metadata, root import, representative submodule imports, `pip check`, and CLI help for `omicverse`, `omicverse-mcp`, and `ov-skill-seeker`. Private environment paths and executable paths are intentionally omitted from this public provenance file.

## Refresh Triggers

Refresh this skill when OmicVerse changes its public module exports, optional dependency groups, console scripts, MCP flags/schema, AnnData slot conventions, spatial reader layouts, external binary wrappers, or major workflow tests/examples.
