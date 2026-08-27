# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a Graph Nets checkout. If the current repo commit, dirty state, package version, dependency family, or major evidence paths differ from this snapshot, refresh the skill before relying on version-sensitive details.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T08:12:48Z",
  "repository": {
    "name": "graph_nets",
    "remote_url": "https://github.com/google-deepmind/graph_nets.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "adf25162ba21bb0ae176c35483a74fb0c9dff576",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "The source package/docs were clean at extraction time; dirty paths were local skill-generation logs, runtime skill files, and review artifacts."
  },
  "packages": [
    {
      "name": "graph-nets",
      "version": "1.1.1.dev0",
      "import_names": ["graph_nets"]
    }
  ],
  "verified_runtime_families": [
    {
      "name": "tensorflow1-sonnet1-cpu",
      "tensorflow": "1.15.5",
      "sonnet": "1.36",
      "networkx": "2.6.3",
      "numpy": "1.18.5",
      "protobuf": "3.19.6"
    },
    {
      "name": "tensorflow2-sonnet2-cpu",
      "tensorflow": "2.2.0",
      "sonnet": "2.0.2",
      "networkx": "2.8.8",
      "numpy": "1.19.5",
      "protobuf": "3.19.6"
    }
  ],
  "evidence": {
    "source_roots": [
      "graph_nets/graphs.py",
      "graph_nets/utils_np.py",
      "graph_nets/utils_tf.py",
      "graph_nets/blocks.py",
      "graph_nets/modules.py",
      "graph_nets/_base.py"
    ],
    "docs": [
      "README.md",
      "docs/index.md",
      "docs/contents.md",
      "docs/graph_nets.md"
    ],
    "examples": [
      "graph_nets/demos/",
      "graph_nets/demos_tf2/"
    ],
    "tests": [
      "graph_nets/tests/",
      "graph_nets/tests_tf2/"
    ],
    "package_metadata": [
      "setup.py"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and refresh it.
- If package source, docs, demos, tests, or setup metadata changed, refresh even when the commit is unchanged.
- If current tasks require unverified current TensorFlow releases, NetworkX 3+, GPU TensorFlow, or full notebook training, re-run environment verification before trusting compatibility guidance.
