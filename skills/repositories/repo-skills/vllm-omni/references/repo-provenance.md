# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of vLLM-Omni. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T06:48:04Z",
  "repository": {
    "name": "vllm-omni",
    "remote_url": "https://github.com/vllm-project/vllm-omni.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "35cacf020c823da56e5ad437128bc4e93a5a3ed1",
    "working_tree": "clean before generated skill files were written",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "vllm-omni",
      "version": "0.1.dev1+g35cacf020",
      "import_names": ["vllm_omni"]
    },
    {
      "name": "vllm",
      "version": "0.26.0",
      "import_names": ["vllm"]
    }
  ],
  "evidence": {
    "source_roots": ["vllm_omni"],
    "docs": ["README.md", "docs/getting_started", "docs/cli", "docs/serving", "docs/configuration", "docs/user_guide", "docs/features", "docs/design", "docs/models/supported_models.md"],
    "examples": ["examples/offline_inference", "examples/online_serving", "recipes"],
    "tests": ["tests/utils", "tests/examples", "tests/diffusion", "tests/core", "tests/e2e"],
    "scripts_and_tools": ["tools/configure_stage_memory.py", "tools/pre_commit/check_tts_adapter.py", "tools/wan22/assemble_wan22_i2v_diffusers.py", "scripts/build_wheel.sh"],
    "metadata": ["pyproject.toml", "setup.py", "requirements/common.txt", "requirements/cuda.txt", "requirements/cpu.txt", "requirements/rocm.txt", "requirements/npu.txt", "requirements/xpu.txt", "requirements/musa.txt"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If source files, package metadata, deploy schemas, CLI entry points, OpenAI protocol classes, or supported model tables changed, refresh the skill even on the same commit.
- If the installed `vllm` major/minor no longer matches the intended vLLM-Omni release line, refresh or update install guidance before running model workflows.
- Ignore untracked generated skill files under a checkout-local `skills/` directory when comparing the original source dirty state.
