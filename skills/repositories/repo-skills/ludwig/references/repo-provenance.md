# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a Ludwig checkout. If the current repo commit, dirty state, package version, CLI inventory, or config schema differs from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T17:27:16Z",
  "repository": {
    "name": "ludwig",
    "remote_url": "https://github.com/ludwig-ai/ludwig.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "5d19f3e632124e2f92266faca773047aeeeb0da4",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "ludwig",
      "version": "0.17.8",
      "import_names": ["ludwig"]
    }
  ],
  "evidence": {
    "source_roots": ["ludwig"],
    "package_metadata": ["pyproject.toml"],
    "docs": ["README.md", "README_KR.md", "RELEASES.md", "docs/developer_guide/adding_a_feature_type.md", "tests/README.md"],
    "examples": ["examples"],
    "tests": ["tests/ludwig", "tests/integration_tests"],
    "configs": ["ludwig/schema", "ludwig/schema/metadata", "schemastore"]
  }
}
```

## Refresh check

- Refresh if `git rev-parse HEAD` differs from the commit above.
- Refresh if package metadata changes the Python requirement, extras, console script, or version source.
- Refresh if `ludwig --help` adds/removes subcommands or if major API signatures in `LudwigModel` change.
- Refresh if optional dependency behavior changes for Ray, FastAPI, KServe, vLLM, ONNX, MLflow, provider SDKs, or LLM/PEFT workflows.
