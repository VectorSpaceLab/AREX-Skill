# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout or
installed release of X-AnyLabeling. If the current commit, dirty state, package
version, public entry points, or major evidence paths differ from this snapshot,
run `refresh-repo-skill` before relying on implementation-specific guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-12T18:54:05Z",
  "repository": {
    "name": "X-AnyLabeling",
    "remote_url": "https://github.com/CVHub520/X-AnyLabeling.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "5f80ec4b8c80f96716c3e8a3753f191e84c19b8c",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "x-anylabeling-cvhub",
      "version": "4.0.2",
      "import_names": ["anylabeling"],
      "console_scripts": ["xanylabeling"]
    }
  ],
  "evidence": {
    "package_metadata": ["pyproject.toml", "MANIFEST.in"],
    "source_roots": [
      "anylabeling/app.py",
      "anylabeling/config.py",
      "anylabeling/views",
      "anylabeling/services/auto_labeling",
      "anylabeling/services/auto_training",
      "anylabeling/configs"
    ],
    "docs": [
      "README.md",
      "docs/en/get_started.md",
      "docs/en/cli.md",
      "docs/en/user_guide.md",
      "docs/en/model_zoo.md",
      "docs/en/custom_model.md",
      "docs/en/image_classifier.md",
      "docs/en/video_classifier.md",
      "docs/en/paddle_ocr.md",
      "docs/en/vqa.md",
      "docs/en/chatbot.md"
    ],
    "examples": ["examples"],
    "tests": [
      "tests/test_utils/test_label_converter.py",
      "tests/test_config/test_normalization.py",
      "tests/test_labeling",
      "tests/test_models"
    ],
    "scripts_and_tools": ["scripts", "tools"],
    "packaging": ["packaging/pyinstaller"]
  },
  "verification_baseline": {
    "python": "3.12",
    "selected_extra": "cpu",
    "verified": [
      "distribution metadata x-anylabeling-cvhub==4.0.2",
      "import anylabeling",
      "xanylabeling version",
      "xanylabeling --help",
      "xanylabeling convert registry with 19 tasks",
      "ONNX Runtime CPUExecutionProvider",
      "ModelManager registry count 204 after config initialization"
    ],
    "not_verified": [
      "CUDA/GPU ONNX Runtime execution",
      "TensorRT execution",
      "model downloads",
      "remote inference service",
      "GUI interactive display",
      "Ultralytics training",
      "PyInstaller builds",
      "translation/resource regeneration"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as
  potentially stale.
- If the package version, `pyproject.toml` optional extras, or the `xanylabeling`
  entry point changes, refresh before relying on install/CLI guidance.
- If `anylabeling/views/common/converter.py` or
  `anylabeling/views/labeling/label_converter.py` changes, refresh conversion
  task and data-format guidance.
- If `anylabeling/services/auto_labeling`, model config YAMLs, or `docs/en/model_zoo.md`
  changes, refresh model registry and custom-model guidance.
- If `anylabeling/services/auto_training`, PyInstaller specs, or build/localization
  scripts change, refresh developer-workflow guidance.
- The `skills/` dirty path in this snapshot is the generated skill/review output
  from construction; other dirty source paths should trigger refresh.
