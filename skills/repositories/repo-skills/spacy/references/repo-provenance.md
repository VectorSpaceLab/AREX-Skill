# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of spaCy. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-10T10:42:16Z",
  "repository": {
    "name": "spaCy",
    "remote_url": "https://github.com/explosion/spaCy.git",
    "vcs": "git",
    "branch": "master",
    "tag": "release-v3.8.15",
    "commit": "f69c32f7a033366ec0d49ec94e5a4feb885d5157",
    "working_tree": "dirty",
    "dirty_paths": [
      "spacy/tests/package/test.cfg",
      "spacy/tests/package/test.toml",
      "spacy/tests/package/test.txt"
    ]
  },
  "packages": [
    {
      "name": "spacy",
      "version": "3.8.15",
      "import_names": ["spacy"]
    }
  ],
  "evidence": {
    "source_roots": ["spacy"],
    "docs": ["README.md", "website/docs"],
    "examples": ["examples", "extra/example_data"],
    "tests": ["spacy/tests"],
    "configs": ["pyproject.toml", "setup.cfg", "setup.py", "requirements.txt", "build-constraints.txt", "spacy/default_config.cfg", "spacy/default_config_pretraining.cfg"]
  },
  "notes": [
    "Generated runtime outputs and review artifacts are construction outputs and are not part of source evidence.",
    "The dirty source paths listed above were already present during repository analysis and are tracked here so refresh checks can compare source-state drift.",
    "Optional accelerator and model-download paths were documented and partially probed, but only the CPU/base package path is verified for this construction run."
  ]
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit, run `refresh-repo-skill`.
