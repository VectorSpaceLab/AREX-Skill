# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of `img2img-turbo`. If the current commit, branch, dirty state, package/runtime facts, or evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T22:36:33Z",
  "repository": {
    "name": "img2img-turbo",
    "remote_url": "https://github.com/GaParmar/img2img-turbo.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "86f54146590ffb4543c8cf85b5a36657da670924",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["pix2pix_turbo", "cyclegan_turbo", "image_prep", "model", "my_utils"],
      "note": "This checkout has no pyproject.toml, setup.py, or setup.cfg; treat it as a source checkout rather than an installable distribution. Import modules from src/ when inspecting the source tree."
    }
  ],
  "evidence": {
    "source_roots": ["src", "src/my_utils"],
    "docs": ["README.md", "docs"],
    "examples": ["gradio_canny2image.py", "gradio_sketch2image.py", "assets/examples"],
    "tests": [],
    "configs": ["environment.yaml", "requirements.txt"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and refresh it.
- If the dirty paths differ in a way that affects source, docs, scripts, configs, or examples, refresh it.
- If the source tree gains packaging metadata, public entry points, or changed workflow flags, refresh it even if the commit is unchanged.
