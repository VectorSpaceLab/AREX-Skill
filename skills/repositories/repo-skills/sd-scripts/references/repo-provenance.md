# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an sd-scripts checkout. If the current repo commit, dirty state, package metadata, or major evidence paths differ from this snapshot, refresh the skill from repository evidence.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "sd-scripts",
    "remote_url": "https://github.com/kohya-ss/sd-scripts.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "c162e9039cc3228057b3fc6ae64ce770b87ab9bf",
    "dirty_state": {
      "status": "dirty-after-generation",
      "notes": "The generated skills/ tree was untracked during skill creation. Source evidence outside skills/ had no listed changes in the captured status output."
    }
  },
  "package": {
    "distribution_name": "library",
    "version": "0.0.0",
    "verified_imports": ["library"],
    "console_entry_points": []
  },
  "evidence_paths": [
    "README.md",
    "README-ja.md",
    "setup.py",
    "requirements.txt",
    "docs/",
    "library/",
    "networks/",
    "tools/",
    "finetune/",
    "tests/",
    "*.py",
    ".ai/"
  ],
  "generated_skill": {
    "id": "sd-scripts",
    "sub_skills": [
      "data-preparation",
      "training",
      "generation",
      "model-utilities"
    ]
  }
}
```

## Refresh Triggers

Refresh this skill when any of these change materially:

- Root training or generation scripts are renamed, removed, or gain new required arguments.
- `requirements.txt`, README installation guidance, or PyTorch/CUDA support changes.
- Dataset config, metadata, validation, or inpainting docs change.
- Model-family docs for SDXL, SD3, FLUX/Chroma, Lumina, HunyuanImage, or Anima change.
- Utility scripts for LoRA merge/extract/convert, checkpoint conversion, or metadata handling change.
- New public workflows are added under `docs/`, root scripts, `tools/`, `networks/`, or `finetune/`.
