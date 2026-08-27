# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a DreamCraft3D checkout. If the current repo commit, dirty state, public configs, source roots, or artifact conventions differ from this snapshot, run `refresh-repo-skill` before relying on the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T06:48:40Z",
  "repository": {
    "name": "DreamCraft3D",
    "remote_url": "https://github.com/deepseek-ai/DreamCraft3D.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "5829ef116d36c871ce2b9e54a6153dd3856a1561",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"],
    "dirty_note": "Dirty state is from generated skill/log artifacts in this production checkout; upstream source evidence was taken from the listed commit."
  },
  "packages": [
    {
      "name": "DreamCraft3D source checkout",
      "version": null,
      "import_names": ["threestudio"],
      "installable_distribution": false
    }
  ],
  "evidence": {
    "source_roots": ["threestudio", "extern/zero123.py", "extern/ldm_zero123"],
    "docs": ["README.md", "docs/installation.md"],
    "configs": [
      "configs/dreamcraft3d-coarse-nerf.yaml",
      "configs/dreamcraft3d-coarse-neus.yaml",
      "configs/dreamcraft3d-geometry.yaml",
      "configs/dreamcraft3d-texture.yaml"
    ],
    "scripts": [
      "launch.py",
      "preprocess_image.py",
      "gradio_app.py",
      "metric_utils.py",
      "threestudio/scripts"
    ],
    "runtime_assets": ["load/images", "load/tets", "load/zero123", "docker"],
    "tests": []
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat the skill as potentially stale.
- If canonical config names, stage order, `launch.py` arguments, image sidecar conventions, or output directory conventions change, refresh the skill.
- If the repo becomes an installable Python distribution or changes package/import names, refresh the install and inspection guidance.
- If Gradio config files are added or removed, refresh the `interfaces-and-monitoring` guidance.
- If new tests/examples are added, refresh native candidate and verification planning.

## Evidence limits

This generation did not run full CUDA DreamCraft3D training, model downloads, DreamBooth/LoRA training, Docker builds, or mesh export from a real checkpoint. The skill contains safe command builders, validators, and troubleshooting guidance, while full runtime execution still depends on the user's CUDA/model environment.
