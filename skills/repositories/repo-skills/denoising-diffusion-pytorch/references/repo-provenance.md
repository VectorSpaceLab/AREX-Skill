# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of `denoising-diffusion-pytorch`. If the current commit, dirty state, package version, or major public API evidence differs from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T00:00:00Z",
  "repository": {
    "name": "denoising-diffusion-pytorch",
    "remote_url": "https://github.com/lucidrains/denoising-diffusion-pytorch.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "faed4db28e724735323fa91c70aa9b28a6e1cbac",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "denoising-diffusion-pytorch",
      "version": "2.3.1",
      "import_names": ["denoising_diffusion_pytorch"]
    }
  ],
  "evidence": {
    "source_roots": ["denoising_diffusion_pytorch"],
    "docs": ["README.md"],
    "examples": ["README.md snippets", "module __main__ examples"],
    "tests": [],
    "configs": ["pyproject.toml"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, refresh the skill.
- If package exports in `denoising_diffusion_pytorch/__init__.py` or constructor signatures change, refresh the skill.
- If dependency metadata or Python support changes, refresh the install/backend guidance.
