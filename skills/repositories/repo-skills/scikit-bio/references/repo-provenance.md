# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-30T00:00:00Z",
  "repository": {
    "name": "scikit-bio",
    "remote_url": "https://github.com/scikit-bio/scikit-bio.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "71520dab98e0e7a482a196c65cb4d4c7bc8efdf5",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "scikit-bio",
      "version": "0.7.4-dev",
      "import_names": ["skbio"]
    }
  ],
  "evidence": {
    "source_roots": [
      "skbio/",
      "skbio/sequence/",
      "skbio/alignment/",
      "skbio/tree/",
      "skbio/diversity/",
      "skbio/table/",
      "skbio/stats/",
      "skbio/io/",
      "skbio/metadata/",
      "skbio/embedding/"
    ],
    "docs": [
      "README.rst",
      "doc/source/sequence.rst",
      "doc/source/alignment.rst",
      "doc/source/tree.rst",
      "doc/source/diversity.rst",
      "doc/source/table.rst",
      "doc/source/stats.rst",
      "doc/source/io.rst",
      "doc/source/metadata.rst",
      "doc/source/embedding.rst",
      "web/install.rst",
      "web/learn.rst",
      "web/devdoc/"
    ],
    "examples": [],
    "tests": [
      "skbio/sequence/tests/",
      "skbio/alignment/tests/",
      "skbio/tree/tests/",
      "skbio/diversity/tests/",
      "skbio/diversity/alpha/tests/",
      "skbio/diversity/beta/tests/",
      "skbio/table/tests/",
      "skbio/stats/tests/",
      "skbio/stats/distance/tests/",
      "skbio/stats/ordination/tests/",
      "skbio/stats/composition/tests/",
      "skbio/io/tests/",
      "skbio/io/format/tests/",
      "skbio/metadata/tests/",
      "skbio/embedding/tests/"
    ],
    "configs": [
      "pyproject.toml",
      "setup.py",
      "MANIFEST.in"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ from the snapshot, decide whether the changes affect public APIs, docs, tests, package metadata, or generated skills. Refresh when they do.
- If `skbio.__version__`, package dependencies, public imports, IO formats, or major module entry points change, run `refresh-repo-skill`.
- If a future checkout removes or substantially rewrites any evidence path above, refresh before relying on the affected sub-skill.
