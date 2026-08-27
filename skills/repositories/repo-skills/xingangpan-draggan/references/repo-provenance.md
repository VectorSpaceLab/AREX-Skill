# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a DragGAN checkout. If the current repo commit, public entry points, dependency files, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T18:15:36Z",
  "repository": {
    "name": "DragGAN",
    "remote_url": "https://github.com/XingangPan/DragGAN.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "336f120ce126aca6f55dc58537e76c10d19eabd0",
    "working_tree": "generated-artifacts-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": [
        "dnnlib",
        "legacy",
        "torch_utils",
        "training",
        "viz",
        "gradio_utils",
        "gui_utils",
        "stylegan_human"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "dnnlib/",
      "torch_utils/",
      "training/",
      "viz/",
      "gui_utils/",
      "gradio_utils/",
      "stylegan_human/"
    ],
    "docs": [
      "README.md",
      "stylegan_human/README.md",
      "stylegan_human/docs/Dataset.md"
    ],
    "examples": [
      "gen_images.py",
      "visualizer_drag.py",
      "visualizer_drag_gradio.py",
      "scripts/",
      "stylegan_human/generate.py",
      "stylegan_human/interpolation.py",
      "stylegan_human/style_mixing.py",
      "stylegan_human/stylemixing_video.py",
      "stylegan_human/bg_white.py",
      "stylegan_human/alignment.py",
      "stylegan_human/run_pti.py",
      "stylegan_human/edit.py",
      "stylegan_human/insetgan.py"
    ],
    "tests": [],
    "configs": [
      "environment.yml",
      "requirements.txt",
      "stylegan_human/environment.yml",
      "stylegan_human/edit/edit_config.py",
      "stylegan_human/pti/pti_configs/"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as potentially stale.
- If any public entry point listed under `evidence.examples` changes flags or import behavior, refresh the skill.
- If dependency files or the StyleGAN-Human config files change, refresh environment and troubleshooting guidance.
- The dirty `skills/` path records generated skill artifacts, not source evidence used to infer DragGAN behavior.
