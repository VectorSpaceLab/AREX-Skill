# Repository Provenance

## Purpose

Read this before deciding whether this Sonnet repo skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "evidence": {
    "configs": [
      "setup.py",
      "requirements.txt",
      "requirements-test.txt",
      "requirements-tf.txt",
      "MANIFEST.in"
    ],
    "docs": [
      "README.md",
      "docs/index.rst",
      "docs/modules.rst",
      "docs/api.rst"
    ],
    "examples": [
      "examples/simple_mnist.py",
      "examples/simple_mnist_test.py",
      "examples/functional_mlp_mnist.py",
      "examples/*.ipynb (reference-only)"
    ],
    "source_roots": [
      "sonnet",
      "sonnet/src",
      "sonnet/src/nets",
      "sonnet/src/functional",
      "sonnet/src/distribute",
      "sonnet/src/optimizers"
    ],
    "tests": [
      "sonnet/src/*_test.py",
      "sonnet/src/nets/*_test.py",
      "sonnet/src/functional/*_test.py",
      "sonnet/src/optimizers/*_test.py",
      "sonnet/src/conformance/*_test.py"
    ]
  },
  "generated_at_utc": "2026-08-13T16:13:15Z",
  "packages": [
    {
      "import_names": [
        "sonnet"
      ],
      "name": "dm-sonnet",
      "version": "2.0.3.dev"
    }
  ],
  "repository": {
    "branch": "v2",
    "commit": "4a3bae0fe2837f68ef74025952ded3074e20592a",
    "dirty_paths": [
      "skills/"
    ],
    "name": "sonnet",
    "remote_url": "https://github.com/google-deepmind/sonnet.git",
    "tag": null,
    "vcs": "git",
    "working_tree": "dirty"
  },
  "schema": "disco.repo-provenance.v1"
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit, refresh the skill.
- This snapshot intentionally records only relative evidence paths and no local Python or environment paths.
