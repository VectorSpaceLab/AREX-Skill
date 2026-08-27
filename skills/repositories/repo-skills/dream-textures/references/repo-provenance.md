# Repository Provenance

## Purpose

Read this before deciding whether this Dream Textures skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T18:16:41Z",
  "repository": {
    "name": "dream-textures",
    "remote_url": "https://github.com/carson-katri/dream-textures.git",
    "vcs": "git",
    "branch": "main",
    "tag": "0.4.1",
    "commit": "c2622a8a9f1ae6b790cfe1d2571f814b126811b4",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "dream-textures",
      "version": "0.4.1",
      "import_names": [
        "dream_textures"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "__init__.py",
      "api/",
      "diffusers_backend.py",
      "engine/",
      "generator_process/",
      "operators/",
      "preferences.py",
      "property_groups/",
      "render_pass.py",
      "ui/"
    ],
    "docs": [
      "README.md",
      "docs/SETUP.md",
      "docs/IMAGE_GENERATION.md",
      "docs/INPAINT_OUTPAINT.md",
      "docs/TEXTURE_PROJECTION.md",
      "docs/RENDER_PASS.md",
      "docs/AI_UPSCALING.md",
      "docs/DEVELOPMENT_ENVIRONMENT.md"
    ],
    "examples": [
      "community_backends/test.py"
    ],
    "tests": [],
    "configs": [
      "requirements/",
      "sd_configs/",
      "builtin_presets/"
    ],
    "scripts": [
      "scripts/train_detect_seamless.py",
      "scripts/zip_dependencies.py"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has non-skill source changes relative to this snapshot, run `refresh-repo-skill`.
- If `bl_info`, `version.py`, public backend signatures, requirement files, setup/model management behavior, or documented workflows change, run `refresh-repo-skill` even when the commit baseline is otherwise familiar.
- If a newer Dream Textures release changes Blender version support, model families, Diffusers APIs, or dependency variants, run `refresh-repo-skill` before relying on this skill for setup or troubleshooting.
