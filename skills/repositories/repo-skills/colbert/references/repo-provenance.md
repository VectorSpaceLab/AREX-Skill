# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T10:40:00Z",
  "repository": {
    "name": "ColBERT",
    "remote_url": "https://github.com/stanford-futuredata/ColBERT.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "cc4f3dc91c0b45d2d08c251d9d95178285c65f1c",
    "working_tree": "dirty",
    "dirty_paths": [
      "colbert_ai.egg-info/",
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "colbert-ai",
      "version": "0.2.22",
      "import_names": ["colbert"]
    }
  ],
  "evidence": {
    "source_roots": ["colbert", "utility", "baleen", "server.py"],
    "docs": ["README.md", "LoTTE.md", "docs/source", "docs/intro.ipynb", "docs/intro2new.ipynb", "docs/intro2updated.ipynb"],
    "tests": ["colbert/tests"],
    "sample_data": ["data/5k-eval.queries.tsv", "data/5k-eval.qrels.tsv"],
    "package_metadata": ["setup.py", "MANIFEST.in", "conda_env.yml", "conda_env_cpu.yml"],
    "existing_skill_evidence": ["skills/colbert"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-skill-from-repo`.
- If the current dirty paths differ from the snapshot, run `refresh-skill-from-repo` before relying on exact API or workflow details.
- If `setup.py`, public imports, constructor signatures, package extras, docs, tests, or source evidence paths changed, refresh this skill even when the commit appears similar.
- If a user works from the legacy `colbertv1` branch or another deprecated branch, treat this skill as main-branch ColBERTv2/PLAID guidance and refresh or create a branch-specific skill.
