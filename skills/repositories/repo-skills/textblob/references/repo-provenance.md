# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
TextBlob repository. If the current repo commit, dirty state, package version,
public APIs, or major evidence paths differ from this snapshot, run
`refresh-repo-skill` before relying on detailed guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-12T18:31:45Z",
  "repository": {
    "name": "TextBlob",
    "remote_url": "https://github.com/sloria/TextBlob.git",
    "vcs": "git",
    "branch": "dev",
    "tag": null,
    "commit": "09cd7bfb00d945978fac2b3e0d5ce7bb1aa03ab2",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "textblob",
      "version": "0.20.1",
      "import_names": ["textblob"]
    }
  ],
  "evidence": {
    "source_roots": ["src/textblob"],
    "docs": [
      "README.rst",
      "docs/install.rst",
      "docs/quickstart.rst",
      "docs/advanced_usage.rst",
      "docs/classifiers.rst",
      "docs/extensions.rst",
      "docs/api_reference.rst"
    ],
    "tests": [
      "tests/test_blob.py",
      "tests/test_classifiers.py",
      "tests/test_formats.py",
      "tests/test_inflect.py",
      "tests/test_np_extractor.py",
      "tests/test_parsers.py",
      "tests/test_sentiments.py",
      "tests/test_taggers.py",
      "tests/test_tokenizers.py",
      "tests/test_decorators.py"
    ],
    "configs": ["pyproject.toml", "tox.ini", ".github/workflows/build-release.yml"],
    "examples": []
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as
  potentially stale.
- If TextBlob's package version, public constructor signatures, default model
  classes, or NLTK corpus names changed, refresh the skill even on the same
  commit.
- The generation checkout was dirty only because generated `skills/` outputs
  were present; source, docs, tests, and package metadata were otherwise taken
  from the commit above.
- If the target checkout has new examples, CLI entry points, extension rules,
  classifier formats, or docs, refresh so bundled references/scripts remain
  self-contained.
