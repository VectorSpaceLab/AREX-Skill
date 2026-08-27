# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public APIs, model-loading behavior, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T16:52:51Z",
  "repository": {
    "name": "Synonyms",
    "remote_url": "https://github.com/chatopera/Synonyms.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "22044ad48b85a0ac1cb1c495a4556d5235799f81",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "synonyms",
      "version": "3.25.1",
      "import_names": ["synonyms"]
    }
  ],
  "evidence": {
    "source_roots": ["synonyms/"],
    "package_metadata": ["setup.py", "setup.cfg", "Requirements.txt"],
    "docs": ["README.md", "CHANGELOG.md", "VALUATION.md", "LICENSE"],
    "examples": ["demo.py", "benchmark.py"],
    "scripts": ["scripts/test.sh", "scripts/package.sh", "scripts/pypi.sh"],
    "tests": [],
    "configs": [],
    "generated_or_excluded": ["assets/", ".github/", ".travis.yml", "skills/"]
  },
  "public_api_signatures_verified": {
    "nearby": "(word, size=10)",
    "compare": "(s1, s2, seg=True, ignore=False, stopwords=False)",
    "display": "(word, size=10)",
    "describe": "()",
    "v": "(word)",
    "sv": "(sentence, ignore=False)",
    "bow": "(sentence, ignore=False)",
    "seg": "(sen, HMM=True)",
    "keywords": "(sentence, topK=5, withWeight=False, allowPOS=())"
  }
}
```

## Refresh check

- If the current Git commit differs from `repository.commit`, treat this skill as potentially stale.
- If `setup.py`, `synonyms/synonyms.py`, `synonyms/word2vec.py`, `synonyms/utils.py`, README install/API docs, or model-loading environment variables changed, refresh the skill.
- The dirty path `skills/` reflects generated production artifacts and was excluded from source extraction. If source code or docs are dirty in a future checkout, refresh before relying on this skill.
- If package version or import-time behavior changes, rerun install/API smoke verification and refresh the references.
