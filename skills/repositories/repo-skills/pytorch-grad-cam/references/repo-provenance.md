# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for another checkout of
`pytorch-grad-cam`. If the commit, dirty state, package version, or evidence
paths differ materially, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T19:24:21Z",
  "repository": {
    "name": "pytorch-grad-cam",
    "remote_url": "https://github.com/jacobgil/pytorch-grad-cam.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "dfca63679d157d576563c15eb0e373d5c97b50b0",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "grad-cam",
      "version": "1.5.5",
      "import_names": ["pytorch_grad_cam"]
    }
  ],
  "evidence": {
    "source_roots": ["pytorch_grad_cam/"],
    "docs": ["README.md", "tutorials/vision_transformers.md", "tutorials/bnnr_saliency_guided_augmentation.md"],
    "examples": ["cam.py", "usage_examples/"],
    "tests": ["tests/"],
    "configs": ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "MANIFEST.in", ".github/workflows/python-app.yml"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, refresh the skill.
- If the dirty path set is materially different, refresh the skill.
- If package metadata or public import signatures change, refresh the skill.
