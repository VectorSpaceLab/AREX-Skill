# Repository Provenance

## Purpose

Read this before deciding whether the Data-Juicer skill is current for a checkout. If the source commit, branch, tag, dirty state, package version, or major evidence paths change, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-09T22:12:35Z",
  "repository": {
    "name": "data-juicer",
    "remote_url": "https://github.com/datajuicer/data-juicer.git",
    "vcs": "git",
    "branch": "main",
    "tag": "v1.5.5",
    "commit": "0e40a8659a759286d9bb3899cb3ef7f6fdbc624c",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "py-data-juicer",
      "version": "1.5.5",
      "import_names": ["data_juicer"],
      "entry_points": ["dj-process", "dj-analyze", "dj-install", "dj-mcp"]
    }
  ],
  "evidence": {
    "source_roots": [
      "data_juicer",
      "docs",
      "demos",
      "tests",
      "tools",
      "scripts",
      "service.py",
      "app.py",
      "pyproject.toml",
      "README.md"
    ],
    "docs": [
      "docs/DJ_service.md",
      "docs/DatasetCfg.md",
      "docs/DeveloperGuide.md",
      "docs/Distributed.md",
      "docs/Export.md",
      "docs/JobManagement.md",
      "docs/OperatorPlugins.md",
      "docs/PartitionAndCheckpoint.md",
      "docs/Tracing.md"
    ],
    "tests": [
      "tests/core/executor/test_partitioned_integration.py",
      "tests/core/executor/test_ray_executor_partitioned.py",
      "tests/tools/test_DJ_mcp_granular_ops.py",
      "tests/tools/test_DJ_mcp_recipe_flow.py",
      "tests/tools/test_mcp_server.py",
      "tests/tools/test_mcp_tool.py",
      "tests/tools/test_op_search.py",
      "tests/tools/test_process_data.py",
      "tests/utils/test_config_utils.py",
      "tests/utils/test_jsonl_lenient_loader.py",
      "tests/utils/test_resource_utils.py",
      "tests/utils/job/test_monitor.py",
      "tests/utils/job/test_snapshot.py",
      "tests/utils/job/test_stopper.py"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, refresh the skill.
- If the package version changes, refresh the skill.
- If the repo introduces new user-facing workflows, optional extras, or service routes, refresh or extend the relevant sub-skill.
