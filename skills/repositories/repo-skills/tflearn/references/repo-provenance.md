# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-12T18:51:28Z",
  "repository": {
    "name": "tflearn",
    "remote_url": "https://github.com/tflearn/tflearn.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "db5176773299b67a2a75c5889fb2aba7fd0fea8a",
    "working_tree": "dirty-generated-skill-artifacts-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "tflearn",
      "version": "0.5.0",
      "import_names": ["tflearn"]
    }
  ],
  "runtime_baseline": {
    "tensorflow": "1.15.5",
    "numpy": "1.18.5",
    "protobuf": "3.20.3",
    "backend": "cpu"
  },
  "evidence": {
    "source_roots": ["tflearn"],
    "docs": ["README.md", "docs/templates", "tutorials/intro"],
    "examples": [
      "examples/basics",
      "examples/extending_tensorflow",
      "examples/images",
      "examples/nlp",
      "examples/others",
      "examples/reinforcement_learning",
      "examples/notebooks"
    ],
    "tests": ["tests"],
    "metadata": ["setup.py", "setup.cfg", ".travis.yml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, public imports, TensorFlow compatibility code, examples, or tests changed even on the same commit, run `refresh-repo-skill`.
- If a checkout's only dirty paths are regenerated `skills/` artifacts, that does not by itself change TFLearn package behavior. Dirty package source, docs, tests, metadata, or examples should trigger a refresh.
- If a future runtime targets TensorFlow 2.x/Keras migration rather than legacy TFLearn use, refresh or extend this skill with explicit migration evidence.
