# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. The repository is a flat script-style project rather than an
installable distribution, so the source commit and runtime TensorFlow version
are the main freshness signals.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T07:34:01Z",
  "repository": {
    "name": "seq2seq-couplet",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "53c3d2592b6c85211936e0ec41a8c2be831c9b58",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "tensorflow",
      "version": "1.15.0",
      "import_names": [
        "tensorflow"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "."
    ],
    "docs": [
      "README.markdown"
    ],
    "examples": [],
    "tests": [],
    "configs": []
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree has source-file changes beyond generated skill or
  review artifacts, run `refresh-repo-skill`.
- If the runtime stack moves away from TensorFlow 1.15 or the project gains a
  real package metadata file, refresh the skill before relying on the old
  install or API guidance.
- If the legacy training or serving scripts are parameterized differently, rerun
  the extraction and verification workflow.
