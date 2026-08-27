# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of FCOS. If the current repo commit, dirty state, package metadata, public APIs, configs, or training/export scripts differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T00:00:00Z",
  "repository": {
    "name": "FCOS",
    "remote_url": "https://github.com/tianzhi0549/FCOS.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "a773f1281275cf1e1cdaa0ca8c4a06b33036bb71",
    "working_tree": "dirty-generated-output-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "fcos",
      "version": "0.1.9",
      "import_names": ["fcos", "fcos_core"]
    }
  ],
  "evidence": {
    "source_roots": ["fcos", "fcos_core"],
    "docs": ["README.md", "INSTALL.md", "MODEL_ZOO.md", "TROUBLESHOOTING.md", "MASKRCNN_README.md", "ABSTRACTIONS.md", "fcos_core/data/README.md"],
    "examples": ["demo", "onnx"],
    "scripts": ["fcos/bin/fcos", "tools/train_net.py", "tools/test_net.py", "tools/remove_solver_states.py", "tools/cityscapes/convert_cityscapes_to_coco.py", "onnx/export_model_to_onnx.py", "onnx/test_fcos_onnx_model.py"],
    "tests": ["tests"],
    "configs": ["configs", "configs/fcos"],
    "package_metadata": ["setup.py", "requirements.txt", "MANIFEST.in"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as potentially stale.
- If package metadata, config keys, public `FCOS` API, source script flags, or compiled extension behavior changed, refresh even when the commit is the same.
- If the only dirty path is a generated `skills/` output directory, the source baseline may still match; if source files under `fcos/`, `fcos_core/`, `configs/`, `tools/`, `demo/`, `onnx/`, or `tests/` are dirty, refresh before relying on exact API or command facts.
