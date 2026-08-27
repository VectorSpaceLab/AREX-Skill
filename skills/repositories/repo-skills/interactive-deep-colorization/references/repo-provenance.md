# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Interactive Deep Colorization. If the current repo commit, dirty state, package metadata, entry points, model layout, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T13:40:34Z",
  "repository": {
    "name": "interactive-deep-colorization",
    "remote_url": "https://github.com/junyanz/interactive-deep-colorization.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "0ee4d11f06d77765d777c0cf90e34278db99e621",
    "working_tree": "dirty-generated-skills-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["data", "models", "ui", "caffe_files"]
    }
  ],
  "evidence": {
    "source_roots": ["data", "models/pytorch", "ui", "caffe_files", "docker/data", "docker/ui_PyQt5"],
    "docs": ["README.md", "docker/README.md"],
    "examples": ["DemoInteractiveColorization.ipynb", "DemoGlobalHistogramTransfer.ipynb", "test_imgs"],
    "scripts": ["ideepcolor.py", "docker/ideepcolor_docker.py", "install", "models/fetch_models.sh", "docker/models/pytorch/fetch_model.sh"],
    "configs": ["models/reference_model/*.prototxt", "models/global_model/*.prototxt"],
    "tests": []
  },
  "construction_verification_summary": {
    "verified": [
      "source imports for data.colorize_image, data.lab_gamut, and models.pytorch.model",
      "selected API signatures",
      "Lab/gamut helper behavior",
      "PyTorch SIGGRAPHGenerator tiny CPU forward",
      "optional torch CUDA visibility"
    ],
    "not_verified": [
      "PyCaffe runtime execution",
      "PyQt GUI launch",
      "Docker build/run",
      "network model downloads",
      "downloaded trained-weight inference",
      "Caffe global histogram native execution"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If source modules under `data/`, `models/pytorch/`, `ui/`, `caffe_files/`, GUI entry scripts, notebooks, model prototxts, or Docker setup files changed, run `refresh-repo-skill`.
- If the current checkout adds packaging metadata, changes CLI defaults, changes model artifact paths, or adds/removes a PyTorch or Caffe workflow, run `refresh-repo-skill`.
- The dirty state in this snapshot reflects generated `skills/` outputs from production; it does not indicate source-code edits to the upstream evidence files.
