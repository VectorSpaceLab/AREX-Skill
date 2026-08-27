# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an AnyLabeling checkout. If the current repo commit, dirty state, package version, public entry points, model catalog, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T16:27:15Z",
  "repository": {
    "name": "anylabeling",
    "remote_url": "https://github.com/vietanhdev/anylabeling.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "5c2ae8fdd03795c9f97f34abe732a9cfc5bf906f",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "The dirty path is repo-local skill production output/log material; source package files used as evidence were not intentionally modified by this skill."
  },
  "packages": [
    {
      "name": "anylabeling",
      "version": "0.4.36",
      "import_names": ["anylabeling"],
      "console_entry_points": ["anylabeling"]
    },
    {
      "name": "anylabeling-gpu",
      "version": "0.4.36",
      "import_names": ["anylabeling"],
      "notes": "Published GPU package is produced from the same source by rewriting package metadata and selecting the GPU dependency variant."
    }
  ],
  "evidence": {
    "source_roots": [
      "anylabeling/",
      "anylabeling/views/",
      "anylabeling/services/auto_labeling/",
      "anylabeling/configs/"
    ],
    "docs": [
      "README.md",
      "anylabeling/README.md",
      "docs/macos_folder_mode.md",
      "CLAUDE.md"
    ],
    "configs": [
      "pyproject.toml",
      "MANIFEST.in",
      "requirements.txt",
      "requirements-gpu.txt",
      "requirements-macos.txt",
      "requirements-dev.txt",
      "anylabeling/configs/anylabeling_config.yaml",
      "anylabeling/configs/auto_labeling/models.yaml"
    ],
    "scripts_and_build": [
      "scripts/compile_languages.py",
      "scripts/generate_languages.py",
      "scripts/build_executable.sh",
      "scripts/build_macos_folder.sh",
      "scripts/build_and_publish_pypi.sh",
      "anylabeling.spec",
      "rthooks/rthook_onnxruntime.py"
    ],
    "tests": [
      "tests/test_label_colormap.py",
      "tests/test_registry.py",
      "tests/test_types.py",
      "tests/test_lru_cache.py",
      "tests/test_model_manager.py",
      "tests/test_sam3_auto_detection.py",
      "tests/test_sam3_onnx_unit.py",
      "tests/test_segment_anything_utils.py",
      "tests/test_canvas_bounded_move.py",
      "tests/test_real_inference.py"
    ],
    "ci": [
      ".github/workflows/tests.yml",
      ".github/workflows/python-publish-cpu.yml",
      ".github/workflows/python-publish-gpu.yml",
      ".github/workflows/release.yml"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as potentially stale.
- If package metadata, `anylabeling.app_info.__version__`, console entry points, dependencies, or model catalog entries changed, refresh the skill even on the same commit.
- If auto-labeling registry keys, SAM/YOLO model classes, label JSON schema, exporter behavior, or PyInstaller/resource scripts changed, refresh the affected sub-skill.
- If the current checkout has source-code dirty paths outside generated skill/log artifacts, refresh or verify against those changes before relying on this skill.
