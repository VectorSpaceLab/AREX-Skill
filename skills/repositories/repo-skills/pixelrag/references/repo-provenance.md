# Repo Provenance

- Schema: `disco.repo-provenance.v1`
- Source repository: PixelRAG
- Public remote: https://github.com/StarTrail-org/PixelRAG.git
- Source commit: `c1dae49ba78e33ff1d02d9f8efd7b9adf9cecb22`
- Branch: `main`
- Exact tag: none detected
- Package version: `pixelrag==0.4.0`
- Working tree state at extraction: dirty only from generated `skills/` output
- Skill id: `pixelrag`
- Skill generated for: DisCo repo-skill operating graph, not project-local task notes

## Evidence paths

Primary package metadata and docs:

- `pyproject.toml`
- `uv.lock`
- `README.md`
- `CLAUDE.md`
- `deploy/README.md`

Runtime source roots:

- `src/pixelrag/`
- `render/src/pixelrag_render/`
- `embed/src/pixelrag_embed/`
- `index/src/pixelrag_index/`
- `serve/src/pixelrag_serve/`

Workflow and behavior evidence:

- `tests/`
- `demos/render/`
- `demos/e2e/`
- `demos/agent_skill.py`
- `eval/README.md`
- `eval/reproduce.sh`
- `eval/serve_up.sh`
- `eval/run_bench.py`
- `eval/lib/`
- `train/README.md`
- `train/pyproject.toml`
- `train/docs/synthetic_data_pipeline.md`
- `plugin/README.md`
- `skill/pixelrag.md`

## Refresh triggers

Refresh this skill when any of these change materially:

- Package version, extras, console scripts, or source roots in `pyproject.toml`.
- Public CLI flags in `pixelshot`, `pixelrag index`, `pixelrag build-index`, or `pixelrag serve`.
- Render tile/chunk manifest schemas or article ID propagation.
- Serve API request/response fields or backend contracts.
- Evaluation ports/tasks/grader behavior in `eval/`.
- Training project pinned versions, released adapter names, or data pipeline ordering.
