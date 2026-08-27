# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of TensorFlow Hub. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on the skill for new work.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T18:55:39Z",
  "repository": {
    "name": "tensorflow-hub",
    "remote_url": "https://github.com/tensorflow/hub.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "26c94f67716f457efaa70c63b4d1b561a08be9f1",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "tensorflow-hub",
      "version": "0.17.0.dev0",
      "source_version": "0.17.0.dev",
      "import_names": ["tensorflow_hub"]
    }
  ],
  "evidence": {
    "source_roots": ["tensorflow_hub/"],
    "docs": ["README.md", "RELEASE.md", "examples/README.md", "docs/README.md"],
    "examples": [
      "examples/text_embeddings_v2/",
      "examples/text_embeddings/",
      "examples/half_plus_two/",
      "examples/image_retraining/README.md"
    ],
    "tests": [
      "tensorflow_hub/*_test.py",
      "examples/text_embeddings_v2/export_test_v2.py",
      "examples/text_embeddings/export_test.py",
      "examples/half_plus_two/half_plus_two_test.py"
    ],
    "configs": [
      "tensorflow_hub/pip_package/setup.py",
      "tensorflow_hub/pip_package/setup.cfg",
      "WORKSPACE"
    ],
    "bundled_runtime_replacements": [
      "sub-skills/load-and-wrap/scripts/smoke_load_and_wrap.py",
      "sub-skills/export-and-save/scripts/export_text_embeddings_v2.py"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is clean while this snapshot was dirty, or if dirty paths differ from the `skills/` generation artifacts recorded here, check whether public package files changed before relying on the skill.
- If `tensorflow_hub/__init__.py`, `tensorflow_hub/module_v2.py`, `tensorflow_hub/keras_layer.py`, `tensorflow_hub/feature_column_v2.py`, `tensorflow_hub/resolver.py`, `examples/text_embeddings_v2/export_v2.py`, or `tensorflow_hub/pip_package/setup.py` changed, refresh this skill.
- If the installed package exposes additional top-level symbols beyond `KerasLayer`, `load`, and `resolve`, refresh the API references.
- If TensorFlow, Keras, or `tf-keras` compatibility behavior changes, refresh the troubleshooting and KerasLayer guidance.
