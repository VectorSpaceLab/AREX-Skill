# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
Zero123Plus repository. If the current repo commit, dirty state, package
metadata, public scripts, or evidence paths differ from this snapshot, run
`refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T14:47:26Z",
  "repository": {
    "name": "zero123plus",
    "remote_url": "https://github.com/SUDO-AI-3D/zero123plus.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "7d0315c31be6eb906b34cf07d91310f8e12e9b95",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "zero123plus",
      "version": null,
      "import_names": []
    }
  ],
  "evidence": {
    "source_roots": [
      "diffusers-support/pipeline.py",
      "examples/",
      "util/"
    ],
    "docs": [
      "README.md",
      "CONTRIBUTING.md"
    ],
    "examples": [
      "examples/img_to_mv.py",
      "examples/depth_controlnet.py",
      "examples/normal_gen.py",
      "examples/matting_postprocess.py",
      "examples/text_to_img.py",
      "resources/examples/"
    ],
    "tests": [],
    "configs": [
      "requirements.txt",
      "cog.yaml",
      "Dockerfile",
      ".gitpod.yml"
    ],
    "deployment_entry_points": [
      "app.py",
      "gradio_app.py",
      "predict.py",
      "download_checkpoints.py"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree's non-generated dirty paths differ from this
  snapshot, review whether the source evidence changed before using the skill.
- If the public model ids, dependency pins, custom pipeline implementation,
  demo scripts, or predictor inputs changed, refresh the skill.

## Package metadata note

The source checkout does not declare a normal Python package version in
`pyproject.toml`, `setup.py`, or `setup.cfg`. The repo skill therefore uses the
Git snapshot plus the dependency/runtime reference as the refresh baseline.
