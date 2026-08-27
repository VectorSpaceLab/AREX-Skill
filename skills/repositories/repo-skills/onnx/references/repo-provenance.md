# Repository Provenance

## Purpose

Read this before deciding whether this ONNX repo skill is current for a checkout or installed package. If the current commit, dirty state, package version, public entry points, or major evidence paths differ materially from this snapshot, run `refresh-repo-skill` before relying on this skill for detailed source-maintenance work.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T16:27:25Z",
  "repository": {
    "name": "onnx",
    "remote_url": "https://github.com/onnx/onnx.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "6a1de3b746e42a0ce194ec27176699c4c160acbd",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "onnx",
      "version": "1.23.0",
      "import_names": ["onnx"]
    }
  ],
  "runtime_facts": {
    "ir_version": 14,
    "default_onnx_opset_version": 28,
    "onnx_ml_opset_version": 5,
    "required_backend": "cpu-or-any"
  },
  "evidence": {
    "package_metadata": ["pyproject.toml", "pixi.toml", "requirements-dev.txt", "requirements-lintrunner.txt"],
    "source_roots": ["onnx/"],
    "public_api_modules": [
      "onnx/__init__.py",
      "onnx/helper.py",
      "onnx/numpy_helper.py",
      "onnx/checker.py",
      "onnx/shape_inference.py",
      "onnx/version_converter.py",
      "onnx/compose.py",
      "onnx/parser.py",
      "onnx/printer.py",
      "onnx/inliner.py",
      "onnx/utils.py",
      "onnx/external_data_helper.py",
      "onnx/model_container.py",
      "onnx/reference/",
      "onnx/backend/"
    ],
    "docs": [
      "README.md",
      "INSTALL.md",
      "CONTRIBUTING.md",
      "SECURITY.md",
      "docs/PythonAPIOverview.md",
      "docs/IR.md",
      "docs/ExternalData.md",
      "docs/ShapeInference.md",
      "docs/VersionConverter.md",
      "docs/Syntax.md",
      "docs/AddNewOp.md",
      "docs/AddFunctionBody.md",
      "docs/OnnxBackendTest.md"
    ],
    "tests": ["tests/python/", "tests/cpp/", "onnx/backend/test/case/"],
    "repo_local_agent_guidance": [".agents/skills/", ".claude/instructions/"],
    "tools": ["tools/", "workflow_scripts/", "onnx/bin/", "onnx/tools/"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as potentially stale.
- If the current checkout has source, docs, metadata, generated-file, or public-entry-point changes beyond generated skill artifacts, refresh this skill.
- If the installed `onnx` version, default opset, IR version, entry points, or optional dependency behavior changed, refresh this skill.
- If a future task depends on newly added operators, generated proto fields, or backend-test behavior after this snapshot, refresh before trusting detailed maintenance guidance.
