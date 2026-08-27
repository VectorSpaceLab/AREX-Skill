# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the BEIR repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T18:46:32Z",
  "repository": {
    "name": "beir",
    "remote_url": "https://github.com/beir-cellar/beir",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "ef83d29307061c65d04b035b4f4e7c18bd8374af",
    "working_tree": "dirty-after-generation",
    "dirty_paths": [
      "skills/"
    ],
    "note": "The source checkout was clean before DisCo generated the runtime skill and review artifacts under skills/."
  },
  "packages": [
    {
      "name": "beir",
      "version": "2.2.0",
      "import_names": ["beir"]
    }
  ],
  "evidence": {
    "source_roots": [
      "beir/datasets",
      "beir/retrieval",
      "beir/reranking",
      "beir/generation",
      "beir/losses",
      "beir/util.py",
      "beir/logging.py"
    ],
    "docs": [
      "README.md",
      "examples/dataset/README.md",
      "examples/retrieval/evaluation/late-interaction/README.md",
      "examples/retrieval/evaluation/reranking/README.md"
    ],
    "examples": [
      "examples/dataset",
      "examples/retrieval/evaluation",
      "examples/retrieval/training",
      "examples/generation",
      "examples/benchmarking",
      "examples/beir-pyserini"
    ],
    "tests": [],
    "configs": [
      "pyproject.toml"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If public package metadata, dependency names, optional extras, or supported Python versions change, refresh the skill even on the same commit.
- If BEIR changes loader schemas, retrieval backend classes, model wrappers, generation outputs, training helpers, or example workflows, refresh the affected sub-skills.
- Ignore differences caused only by generated `skills/` review artifacts unless they also change public BEIR evidence files.
