# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a Gensim checkout. If
the current repo commit, dirty state, package version, or major evidence paths
differ from this snapshot, run `refresh-repo-skill` before relying on this skill
for repository-specific details.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T17:00:29Z",
  "repository": {
    "name": "gensim",
    "remote_url": "https://github.com/piskvorky/gensim.git",
    "vcs": "git",
    "branch": "develop",
    "tag": null,
    "commit": "37f90ec121eb7cd401448a947e80953e0c53ccdc",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "gensim",
      "version": "4.4.0",
      "import_names": ["gensim"]
    }
  ],
  "evidence": {
    "source_roots": ["gensim"],
    "docs": [
      "README.md",
      "docs/src/auto_examples",
      "docs/src/corpora",
      "docs/src/models",
      "docs/src/similarities",
      "docs/src/scripts",
      "docs/src/topic_coherence",
      "docs/src/downloader.rst",
      "docs/src/distributed.rst"
    ],
    "examples": ["docs/src/auto_examples", "gensim/examples"],
    "tests": ["gensim/test"],
    "scripts": ["gensim/scripts"],
    "configs": ["pyproject.toml", "setup.py", "setup.cfg", "MANIFEST.in", "requirements_docs.txt"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the
  snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata, public imports, optional extras, or script/CLI behavior
  changed even on the same commit, run `refresh-repo-skill`.

## Scope decisions recorded at creation

- Included public package workflows: corpora/vector spaces, topic models and
  transformations, embeddings/phrases, similarity retrieval, downloader/data
  helpers, and package scripts.
- Excluded from runtime guidance: release automation, CI/wheel infrastructure,
  generated documentation assets, large/binary test fixtures except as evidence,
  and notebook-heavy or network-heavy examples unless distilled into bundled
  references.
- Required backend: CPU/base scientific Python. Optional dependencies are
  documented but not required for the base skill.
