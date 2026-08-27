# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of PyTorch Geometric Temporal. If the current repo commit, source dirty state, package metadata, public exports, docs, examples, or tests differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T07:39:16Z",
  "repository": {
    "name": "pytorch_geometric_temporal",
    "remote_url": "https://github.com/benedekrozemberczki/pytorch_geometric_temporal.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "ea40a6a396b6688a94d7482d9d5fd288eaa2cb3b",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": [],
    "post_generation_note": "The generated skills/ output was created after the source snapshot and is not part of the upstream source baseline."
  },
  "packages": [
    {
      "name": "torch_geometric_temporal",
      "version": "0.56.2",
      "import_names": ["torch_geometric_temporal"],
      "import_version_constant": "0.54.0"
    }
  ],
  "evidence": {
    "source_roots": [
      "torch_geometric_temporal/"
    ],
    "docs": [
      "README.md",
      "docs/source/index.rst",
      "docs/source/notes/installation.rst",
      "docs/source/notes/introduction.rst",
      "docs/source/modules/root.rst",
      "docs/source/modules/signal.rst",
      "docs/source/modules/dataset.rst"
    ],
    "examples": [
      "examples/recurrent/",
      "examples/indexBatching/"
    ],
    "tests": [
      "test/dataset_test.py",
      "test/batch_test.py",
      "test/recurrent_test.py",
      "test/attention_test.py",
      "test/heterogeneous_test.py",
      "test/index_test.py"
    ],
    "metadata": [
      "setup.py",
      ".github/workflows/main.yml"
    ],
    "datasets": [
      "dataset/"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the commit above, treat this skill as potentially stale.
- If package metadata, exported classes, constructor signatures, or public extras changed, refresh the skill even on the same commit.
- If loader URLs or availability changed, especially traffic, PeMS, Windmill, or synthetic PDE loaders, refresh the dataset-loader and index-batching references.
- If PyTorch Geometric or PyTorch compatibility changes make a bundled smoke script fail, refresh the affected sub-skill.
