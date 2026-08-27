# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a PINTO_model_zoo checkout. If the current repo commit, dirty state, model catalog, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T03:20:00Z",
  "repository": {
    "name": "PINTO_model_zoo",
    "remote_url": "https://github.com/PINTO0309/PINTO_model_zoo.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "833f8d2d27952365157e064d43e0fcd8a41992e3",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": []
    }
  ],
  "evidence": {
    "source_roots": [],
    "docs": [
      "README.md",
      "*/README.md"
    ],
    "examples": [
      "README.md sample sections",
      "numbered model directories containing demo/test scripts"
    ],
    "tests": [
      "representative test_*.py scripts inside numbered model directories"
    ],
    "configs": [
      "model-specific support files such as labels, anchors, priors, json, npy, xml/bin pairs"
    ],
    "scripts": [
      "download*.sh",
      "*quant*.py",
      "*tflite*.py",
      "*onnx*.py",
      "*openvino*.py",
      "*coreml*.py",
      "demo*.py",
      "test*.py"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree contains source changes outside generated `skills/` artifacts, review whether catalog entries, scripts, or folder conventions changed and refresh if they did.
- If the bundled `references/model-catalog.json` no longer matches the current README tables or numbered model directories, refresh the skill before relying on exact search results.
- If a task depends on a concrete model folder added after this snapshot, refresh or extend the skill with that folder's evidence.
