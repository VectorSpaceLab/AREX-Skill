# Repository Provenance

## Purpose

Read this before deciding whether this TensorFlowOnSpark skill is current for a checkout of the repository. If the current repo commit, package metadata, public APIs, examples, tests, or Spark/TensorFlow compatibility surface differ from this snapshot, refresh the skill before relying on it.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T17:46:22Z",
  "repository": {
    "name": "TensorFlowOnSpark",
    "remote_url": "https://github.com/yahoo/TensorFlowOnSpark.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "f9c3e5e58bdb5f8d64ac21399dcf32f612ce67f0",
    "working_tree": "dirty-generated-output-only",
    "dirty_paths": [
      "generated skill and review-output directories created after the source snapshot"
    ]
  },
  "packages": [
    {
      "name": "tensorflowonspark",
      "version": "2.2.5",
      "import_names": ["tensorflowonspark"]
    }
  ],
  "evidence": {
    "source_roots": ["tensorflowonspark/"],
    "docs": ["README.md", "doc/source/"],
    "examples": ["examples/mnist/", "examples/resnet/", "examples/segmentation/"],
    "tests": ["tests/"],
    "scripts": ["scripts/", "examples/utils/"],
    "package_metadata": ["setup.py", "setup.cfg", "requirements.txt", "tox.ini"],
    "runtime_assets": ["lib/tensorflow-hadoop-1.0-SNAPSHOT.jar"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package version, source module names, public signatures, example arguments, Spark/TensorFlow dependency expectations, or the Hadoop TFRecord jar layout changed, refresh the skill even on the same commit.
- If current dirty paths include source, docs, examples, tests, package metadata, or runtime assets outside generated skill/artifact output, refresh before using the skill for precise API or command guidance.
- If the current environment uses TensorFlow 1.x examples, older Spark, or a GPU-specific TensorFlow build, use this skill's compatibility notes but verify the relevant runtime directly.
