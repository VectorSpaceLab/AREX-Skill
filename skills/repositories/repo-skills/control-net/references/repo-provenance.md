# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package/version facts, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-24T00:00:00Z",
  "repository": {
    "name": "ControlNet",
    "remote_url": "https://github.com/lllyasviel/ControlNet",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "ed85cd1e25a5ed592f7d8178495b4483de0331bf",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["cldm", "ldm", "annotator"],
      "note": "The repository has no pyproject.toml, setup.py, or setup.cfg; treat it as a source checkout rather than an installable distribution."
    }
  ],
  "evidence": {
    "source_roots": ["cldm", "ldm", "annotator"],
    "docs": ["README.md", "docs/annotator.md", "docs/faq.md", "docs/low_vram.md", "docs/train.md"],
    "examples_and_scripts": [
      "gradio_annotator.py",
      "gradio_canny2image.py",
      "gradio_depth2image.py",
      "gradio_fake_scribble2image.py",
      "gradio_hed2image.py",
      "gradio_hough2image.py",
      "gradio_normal2image.py",
      "gradio_pose2image.py",
      "gradio_scribble2image.py",
      "gradio_scribble2image_interactive.py",
      "gradio_seg2image.py",
      "tool_add_control.py",
      "tool_add_control_sd21.py",
      "tool_transfer_control.py",
      "tutorial_dataset.py",
      "tutorial_dataset_test.py",
      "tutorial_train.py",
      "tutorial_train_sd21.py"
    ],
    "configs": ["environment.yaml", "models/cldm_v15.yaml", "models/cldm_v21.yaml"],
    "fixtures": ["test_imgs"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source/docs/config/script dirty paths beyond generated `skills/` artifacts, run `refresh-repo-skill`.
- If package metadata appears later, or public entry scripts/configs change, run `refresh-repo-skill`.
- If model/checkpoint names, detector checkpoint expectations, or Gradio app parameters change, run `refresh-repo-skill`.
