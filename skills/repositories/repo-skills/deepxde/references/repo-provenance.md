# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the DeepXDE repository. If the current commit, dirty state, package version, public APIs, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T04:05:44Z",
  "repository": {
    "name": "deepxde",
    "remote_url": "https://github.com/lululxvi/deepxde.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "91bda9aafb8b1c1ea7e932c232ad4880a088f7f3",
    "working_tree": "dirty-generated-skill-artifacts",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "DeepXDE",
      "version": "0.1.dev1+g91bda9aaf",
      "import_names": ["deepxde"]
    }
  ],
  "evidence": {
    "source_roots": ["deepxde/"],
    "docs": [
      "README.md",
      "docs/user/installation.rst",
      "docs/user/faq.rst",
      "docs/user/parallel.rst",
      "docs/demos/",
      "docs/modules/"
    ],
    "examples": [
      "examples/function/",
      "examples/pinn_forward/",
      "examples/pinn_inverse/",
      "examples/operator/",
      "examples/sample_to_test.py"
    ],
    "tests": [],
    "configs": [
      "pyproject.toml",
      "requirements.txt",
      ".github/workflows/build.yml"
    ],
    "existing_repo_skill_evidence": [
      "skills/deepxde.log"
    ]
  },
  "verification_baseline": {
    "backend_verified": "pytorch-cpu",
    "optional_backends_not_verified": [
      "tensorflow.compat.v1",
      "tensorflow",
      "jax",
      "paddle",
      "cuda/gpu",
      "horovod/mpi"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and the changed paths are not limited to generated skill/review artifacts, refresh before trusting API details.
- If package metadata, backend dependency declarations, public entry points, or constructor signatures changed, refresh this skill.
- If a target task depends on a backend that was not verified in this snapshot, run a target-environment backend check before relying on backend-specific behavior.
