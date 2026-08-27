# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of YOLOP. If the current repo commit, dirty state, public workflow files, or package/import layout differ from this snapshot, run `refresh-repo-skill` before relying on file-level guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T10:28:28Z",
  "repository": {
    "name": "YOLOP",
    "remote_url": "https://github.com/hustvl/YOLOP.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "8d8f68df318c71f01d6f813c024df646c7d1978f",
    "working_tree": "dirty-generated-output-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "YOLOP",
      "version": null,
      "import_names": ["lib"]
    }
  ],
  "evidence": {
    "source_roots": ["lib"],
    "docs": ["README.md", "README _CH.md"],
    "examples": ["inference/images", "test.jpg"],
    "tests": [],
    "configs": ["lib/config/default.py"],
    "scripts": [
      "tools/train.py",
      "tools/test.py",
      "tools/demo.py",
      "export_onnx.py",
      "test_onnx.py",
      "hubconf.py",
      "toolkits/datasetpre/gen_bdd_seglabel.py",
      "toolkits/deploy/gen_wts.py",
      "toolkits/deploy/CMakeLists.txt",
      "toolkits/deploy/main.cpp"
    ],
    "artifacts": ["weights/End-to-end.pth", "weights/yolop-320-320.onnx", "weights/yolop-640-640.onnx", "weights/yolop-1280-1280.onnx"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current checkout changes `lib/config/default.py`, `lib/models/YOLOP.py`, `lib/models/common.py`, `tools/*.py`, `export_onnx.py`, `test_onnx.py`, or `toolkits/*`, refresh before trusting detailed workflow guidance.
- If a checkout adds packaging metadata, console entry points, new configuration files, or new model variants, refresh so the skill can stop treating YOLOP as source-root-only.
- If the current working tree is dirty for reasons other than generated `skills/` output, inspect those changes before using this skill for exact commands.
