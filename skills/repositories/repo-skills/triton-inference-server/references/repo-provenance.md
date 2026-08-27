# Repository Provenance

Read this before deciding whether this skill is current for a checkout of NVIDIA Triton Inference Server. If the current repo commit, dirty state, package version, public runtime package versions, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T02:20:00Z",
  "repository": {
    "name": "triton-inference-server",
    "remote_url": "https://github.com/triton-inference-server/server.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "d4d9eb36afcbd0a89428697ced093a4492cf895a",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {"name": "triton-inference-server", "version": "2.72.0dev", "import_names": []},
    {"name": "tritonserver", "version": "2.71.0", "import_names": ["tritonserver"]},
    {"name": "tritonfrontend", "version": "2.71.0", "import_names": ["tritonfrontend"]},
    {"name": "tritonclient", "version": "2.71.0", "import_names": ["tritonclient"]}
  ],
  "evidence": {
    "source_roots": ["src", "src/python/tritonfrontend", "python/openai/openai_frontend"],
    "docs": ["README.md", "docs/README.md", "docs/getting_started", "docs/user_guide", "docs/customization_guide", "docs/protocol", "docs/client_guide", "docs/perf_benchmark", "docs/llm_features"],
    "examples": ["docs/examples", "src/python/examples/example.py"],
    "tests": ["python/openai/tests", "qa/L0_python_api/test_kserve.py", "representative qa/L0_* model, protocol, metrics, OpenAI, and config tests"],
    "configs": ["docs/examples/model_repository", "TRITON_VERSION", "src/python/setup.py", "python/openai/requirements.txt", "python/openai/requirements-test.txt"],
    "scripts_and_tools": ["build.py", "compose.py", "tools/build/build_presets.py", "docs/examples/fetch_models.sh", "docker", "deploy"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale.
- If source, docs, config, package, Docker, deployment, or build behavior changed beyond generated skill artifacts, refresh the skill.
- If `TRITON_VERSION`, public container tags, Python package versions, CLI flags, `tritonfrontend` option signatures, OpenAI frontend endpoints, or model repository/config semantics changed, refresh the skill.
