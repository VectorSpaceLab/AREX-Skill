# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T17:25:30Z",
  "repository": {
    "name": "dm-haiku",
    "remote_url": "https://github.com/google-deepmind/dm-haiku.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "4cd134acd2d50b06b4652b7fa9371e10486e9fa6",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "The source checkout had generated skill/log artifacts under skills/ during construction. Public package source, docs, examples, and tests were otherwise used from the recorded commit."
  },
  "packages": [
    {
      "name": "dm-haiku",
      "version": "0.0.18.dev",
      "installed_distribution_version_seen_during_construction": "0.0.18.dev0",
      "import_names": ["haiku"]
    }
  ],
  "evidence": {
    "source_roots": [
      "haiku/",
      "haiku/_src/",
      "haiku/_src/nets/",
      "haiku/_src/flax/"
    ],
    "docs": [
      "README.md",
      "docs/index.rst",
      "docs/api.rst",
      "docs/notebooks/"
    ],
    "examples": [
      "examples/README.md",
      "examples/mnist.py",
      "examples/vae.py",
      "examples/imagenet/",
      "examples/impala/",
      "examples/rnn/",
      "examples/transformer/"
    ],
    "tests": [
      "haiku/_src/*_test.py",
      "haiku/_src/nets/*_test.py",
      "haiku/_src/flax/*_test.py",
      "haiku/_src/integration/*_test.py"
    ],
    "package_metadata": [
      "setup.py",
      "requirements.txt",
      "requirements-jax.txt",
      "requirements-flax.txt",
      "requirements-test.txt",
      "MANIFEST.in"
    ],
    "repo_scripts_reviewed": [
      "test.sh",
      "docs/Makefile",
      "docs/ext/coverage_check.py"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, public `haiku.__all__`, major docs, or example/test behavior changed, refresh even if the commit is the same.
- If the current checkout has dirty paths outside generated skill/log artifacts, refresh or inspect whether those changes alter public package behavior.
- If a future release changes JAX or Flax compatibility materially, refresh the install and troubleshooting guidance.
