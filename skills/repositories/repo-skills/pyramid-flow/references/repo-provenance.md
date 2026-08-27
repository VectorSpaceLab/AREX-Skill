# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Pyramid-Flow. If the current repo commit, dirty state, package snapshot, or evidence paths differ from this baseline, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T19:59:52Z",
  "repository": {
    "name": "Pyramid-Flow",
    "remote_url": "https://github.com/jy0205/Pyramid-Flow.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "a012faa1dc4d71301a7a153c7f9554c081947ea2",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "Pyramid-Flow runtime modules",
      "version": null,
      "import_names": ["pyramid_dit", "video_vae", "dataset", "diffusion_schedulers", "trainer_misc"]
    }
  ],
  "evidence": {
    "source_roots": [
      "pyramid_dit",
      "video_vae",
      "dataset",
      "diffusion_schedulers",
      "trainer_misc",
      "train",
      "tools"
    ],
    "docs": [
      "README.md",
      "docs/DiT.md",
      "docs/VAE.md"
    ],
    "examples": [
      "app.py",
      "app_multigpu.py",
      "inference_multigpu.py",
      "video_generation_demo.ipynb",
      "image_generation_demo.ipynb",
      "causal_video_vae_demo.ipynb"
    ],
    "scripts": [
      "scripts/inference_multigpu.sh",
      "scripts/app_multigpu_engine.sh",
      "scripts/extract_text_feature.sh",
      "scripts/extract_vae_latent.sh",
      "scripts/train_pyramid_flow.sh",
      "scripts/train_pyramid_flow_without_ar.sh",
      "scripts/train_causal_video_vae.sh"
    ],
    "tests": [
      "annotation/image_text.jsonl",
      "annotation/video_text.jsonl"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the dirty paths differ materially, run `refresh-repo-skill`.
- If the public entry points, import roots, workflow families, or dependency baseline change, run `refresh-repo-skill`.
- If new user-facing repository workflows are added that affect routing, generation, precompute, or training coverage, refresh the skill and its routing metadata together.
