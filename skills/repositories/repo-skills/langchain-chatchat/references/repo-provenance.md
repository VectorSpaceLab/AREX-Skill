# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Langchain-Chatchat. If the current repo commit, dirty state, package version, CLI surface, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on this skill for source-specific work.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T06:05:01Z",
  "repository": {
    "name": "Langchain-Chatchat",
    "remote_url": "https://github.com/chatchat-space/Langchain-Chatchat.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "49165d6af4438aa7e8a1f71ce276db55f4405151",
    "working_tree": "clean-before-generated-skill-artifacts",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "langchain-chatchat",
      "version": "0.3.1.3",
      "import_names": ["chatchat", "langchain_chatchat"],
      "entry_points": ["chatchat = chatchat.cli:main"]
    },
    {
      "name": "open_langchain_chatchat metadata; editable inspection reports open_chatcaht",
      "version": "0.3.0.20240708 in package metadata; 0.0.0 in editable inspection metadata",
      "import_names": ["open_chatcaht"]
    }
  ],
  "evidence": {
    "source_roots": [
      "libs/chatchat-server/chatchat",
      "libs/chatchat-server/langchain_chatchat",
      "libs/python-sdk/open_chatcaht"
    ],
    "package_metadata": [
      "pyproject.toml",
      "libs/chatchat-server/pyproject.toml",
      "libs/python-sdk/pyproject.toml"
    ],
    "docs": [
      "README.md",
      "README_en.md",
      "libs/chatchat-server/README.md",
      "docs/contributing/README_dev.md",
      "docs/contributing/api.md",
      "docs/contributing/settings.md",
      "docs/install/README_docker.md",
      "docs/install/README_xinference.md"
    ],
    "api_and_cli_sources": [
      "libs/chatchat-server/chatchat/cli.py",
      "libs/chatchat-server/chatchat/init_database.py",
      "libs/chatchat-server/chatchat/startup.py",
      "libs/chatchat-server/chatchat/settings.py",
      "libs/chatchat-server/chatchat/server/api_server"
    ],
    "sdk_sources": [
      "libs/python-sdk/open_chatcaht/api_client.py",
      "libs/python-sdk/open_chatcaht/chatchat_api.py",
      "libs/python-sdk/open_chatcaht/api"
    ],
    "tests": [
      "libs/chatchat-server/tests/unit_tests/test_sdk_import.py",
      "libs/chatchat-server/tests/unit_tests/test_mcp_prompts.py",
      "libs/chatchat-server/tests/kb_vector_db/test_faiss_kb.py",
      "libs/python-sdk/tests"
    ],
    "scripts_and_configs": [
      "tools/model_loaders/xinference_manager.py",
      "tools/autodl_start_script",
      "docker/docker-compose.yaml"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as potentially stale.
- If package metadata changes the `chatchat` CLI, `chatchat.settings`, API route files, or SDK import/package names, refresh this skill.
- If the SDK import spelling is corrected upstream, refresh the SDK guidance because this skill intentionally documents the inspected `open_chatcaht` spelling.
- If model-provider or vector-store defaults change, refresh `server-setup-and-cli` and `knowledge-base-and-api` references.
