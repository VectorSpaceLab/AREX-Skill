# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, dependency stack, or major
evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T12:17:45Z",
  "repository": {
    "name": "cs230-code-examples",
    "remote_url": "https://github.com/cs230-stanford/cs230-code-examples.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "478e747b1c8bf57c6e2ce6b7ffd8068fe0287056",
    "working_tree": "dirty",
    "dirty_paths": ["skills/disco/", "skills/tests/"]
  },
  "packages": [
    {
      "name": "torch",
      "version": "1.13.1",
      "import_names": ["torch", "torchvision"]
    },
    {
      "name": "tensorflow",
      "version": "1.15.0",
      "import_names": ["tensorflow"]
    }
  ],
  "evidence": {
    "source_roots": ["pytorch/vision", "pytorch/nlp", "tensorflow/vision", "tensorflow/nlp"],
    "docs": ["README.md", "pytorch/vision/README.md", "pytorch/nlp/README.md", "tensorflow/vision/README.md", "tensorflow/nlp/README.md"],
    "examples": ["pytorch/vision", "pytorch/nlp", "tensorflow/vision", "tensorflow/nlp"],
    "tests": [],
    "configs": ["pytorch/vision/experiments", "pytorch/nlp/experiments", "tensorflow/vision/experiments", "tensorflow/nlp/experiments"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, the skill may be
  stale.
- If the current working tree is clean but this snapshot is dirty, or the dirty
  paths differ materially, refresh the skill.
- If the example dependencies or their major versions change, refresh the skill.
- If the framework example directories change shape or move, refresh the skill.

## Notes

- This repository is a code-example bundle, not a single installable package.
- The generated skill is organized around the PyTorch and TensorFlow example
  trees rather than a top-level Python distribution.
