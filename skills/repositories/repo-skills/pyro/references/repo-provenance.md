# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
Pyro repository. If the current repo commit, dirty state, package version, or
major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T17:31:49Z",
  "repository": {
    "name": "pyro",
    "remote_url": "https://github.com/pyro-ppl/pyro.git",
    "vcs": "git",
    "branch": "dev",
    "tag": null,
    "commit": "1af296c78b8e150b3b7da4ba2f04c45617ba753b",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "pyro-ppl",
      "version": "1.9.1+1af296c",
      "import_names": ["pyro"]
    },
    {
      "name": "pyro-api",
      "version": "0.1.2",
      "import_names": ["pyroapi"]
    }
  ],
  "evidence": {
    "source_roots": [
      "pyro/",
      "pyro/contrib/",
      "pyro/distributions/",
      "pyro/infer/",
      "pyro/nn/",
      "pyro/ops/",
      "pyro/optim/",
      "pyro/params/",
      "pyro/poutine/"
    ],
    "docs": [
      "README.md",
      "docs/source/"
    ],
    "examples": [
      "examples/",
      "tutorial/source/"
    ],
    "tests": [
      "tests/"
    ],
    "configs": [
      "setup.py",
      "setup.cfg",
      "pyproject.toml",
      "MANIFEST.in",
      "Makefile",
      "docs/requirements.txt"
    ],
    "repo_scripts_considered": [
      "scripts/install_pytorch.sh",
      "scripts/perf_test.sh",
      "scripts/profile_model.sh",
      "scripts/update_headers.py",
      "scripts/update_version.py"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree has changes outside the generated `skills/`
  subtree, or generated skill files have been edited independently of a refresh,
  run `refresh-repo-skill`.
- If package metadata, supported Python versions, optional extras, public import
  names, or major public modules changed, run `refresh-repo-skill`.
- If Pyro's contrib modules or inference APIs changed in a way that affects the
  routed sub-skills, refresh before relying on this skill for new code.

## Evidence Notes

- The package has no console-script entry points in this snapshot.
- The minimum verified construction environment covered CPU import, primitives,
  distributions, inference, poutine, Pyro modules/optimizers, a tiny SVI smoke,
  and focused primitive/settings tests.
- CUDA, Funsor, Horovod, Lightning, Graphviz, torchvision, pandas, scanpy, and
  other optional example/tutorial dependencies were treated as optional surfaces
  rather than required verification gates for this skill.
