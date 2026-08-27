# Repository Provenance

Read this before deciding whether this generated skill is current for a
DataChain checkout. If the current commit, dirty source files, package metadata,
public entry points, optional extras, CLI flags, or backend behavior differ from
this snapshot, run `refresh-repo-skill` before treating the guidance as
complete.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18",
  "repository": {
    "name": "datachain",
    "remote_url": "https://github.com/datachain-ai/datachain.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "2deea055a9ca44f46392bf643a5f2762ac88e383",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths_summary": ["skills/ generated during repo-skill production"]
  },
  "packages": [
    {
      "name": "datachain",
      "version": "0.1.dev1+g2deea055a",
      "import_names": ["datachain"],
      "console_scripts": {"datachain": "datachain.cli:main"},
      "requires_python": ">=3.10"
    }
  ],
  "baseline_backend": {
    "required": ["cpu", "sqlite-local"],
    "optional_or_credentialed": [
      "S3/GCS/Azure/Hugging Face storage services",
      "DataChain Studio auth/jobs/pipelines",
      "LLM provider calls",
      "PyTorch/HF/video/audio/vector/Postgres/Zarr extras",
      "ClickHouse or future non-SQLite backend runtime parity"
    ]
  }
}
```

## Evidence Paths

| Category | Relative evidence paths |
| --- | --- |
| Package metadata | `pyproject.toml`, `noxfile.py`, `.pre-commit-config.yaml` |
| Durable maintainer guidance | `AGENT.md`, `CLAUDE.md`, `docs/contributing.md` |
| Public package/root API | `src/datachain/__init__.py`, `src/datachain/lib/dc/`, `src/datachain/lib/data_model.py`, `src/datachain/lib/file.py`, `src/datachain/lib/udf.py` |
| Query engine and schema mapping | `src/datachain/func/`, `src/datachain/sql/`, `src/datachain/query/`, `src/datachain/lib/signal_schema.py`, `src/datachain/lib/convert/` |
| LLM and optional integrations | `src/datachain/llm/`, `src/datachain/toolkit/`, `src/datachain/torch/`, `src/datachain/model/`, `src/datachain/lib/{audio,video,hf,zarr,pytorch,clip,image,text}.py` |
| CLI and Studio | `src/datachain/cli/`, `src/datachain/studio.py`, `src/datachain/remote/studio.py`, `src/datachain/config.py`, `docs/commands/`, `docs/studio/`, `docs/guide/env.md` |
| Agent harness and knowledge base | `src/datachain/skill/`, `docs/getting-started/agents.md`, `docs/harness.md`, `docs/guide/knowledge-base.md`, `docs/use-cases/` |
| Public docs and examples | `README.md`, `docs/concepts/`, `docs/guide/`, `docs/references/`, `examples/` |
| Behavior tests | `tests/unit/`, `tests/func/`, selected top-level CLI/Studio/job/query e2e tests, `tests/examples/` as optional-extra evidence |

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat the skill as
  potentially stale.
- If `git status --short` includes source, docs, tests, or config paths other
  than generated skill artifacts, refresh after the source change is complete.
- If package extras, CLI target layouts, `datachain.llm` signatures, storage
  provider behavior, backend conversion rules, or bundled DataChain skills
  changed, refresh even if the checkout commit was manually patched.
- Baseline verification covers CPU/local SQLite. Backend-specific claims still
  require target backend evidence.
