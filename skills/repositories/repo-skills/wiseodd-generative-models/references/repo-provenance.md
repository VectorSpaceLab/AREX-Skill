# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, dependency baseline, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T17:36:39Z",
  "repository": {
    "name": "generative-models",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "b930d5fa9e2f69adfd4ea8ec759f38f6ce6da4c2",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [],
  "evidence": {
    "source_roots": [],
    "docs": ["README.md", "RBM/README.md", "HelmholtzMachine/README.md"],
    "examples": ["GAN", "VAE", "RBM", "HelmholtzMachine"],
    "tests": [],
    "configs": ["environment.yml"],
    "scripts": ["GAN/**/*.py", "VAE/**/*.py", "RBM/*.py", "HelmholtzMachine/vanilla_HM/helmholtz.py"],
    "existing_skills": ["skills/generative-models.log"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If the top-level family layout changes, update `references/model-catalog.json` and rerun the compatibility checks.
- If dependency guidance changes from the historical `environment.yml`, update `references/compatibility.md` and `scripts/check_legacy_stack.py`.
