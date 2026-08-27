# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Flash Linear Attention. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T07:48:03Z",
  "repository": {
    "name": "flash-linear-attention",
    "remote_url": "https://github.com/fla-org/flash-linear-attention.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "7464b829058a486bfb222de4828ebe3d0b1d17c2",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "flash-linear-attention",
      "version": "0.5.2",
      "import_names": ["fla"]
    }
  ],
  "evidence": {
    "source_roots": ["fla/ops", "fla/modules", "fla/layers", "fla/models", "fla/utils"],
    "docs": ["README.md", "INSTALL.md", "ENVs.md", "FAQs.md", "CONTRIBUTING.md", "AGENTS.md"],
    "examples": ["examples/training.md"],
    "tests": ["tests/ops", "tests/modules", "tests/layers", "tests/models", "tests/context_parallel", "tests/test_public_api.py"],
    "benchmarks": ["benchmarks/ops", "benchmarks/modules", "benchmarks/benchmark_generation.py", "benchmarks/benchmark_training_throughput.py", "benchmarks/visualize.py"],
    "scripts": ["scripts/check_gpu.py", "scripts/find_dependent_tests.py", "scripts/run_benchmark_compare.py", "scripts/extract_triton_autotune_cache.py", "scripts/check_header.py"],
    "repo_local_agent_guidance": [".agents/skills", "AGENTS.md"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the working tree is dirty and the changed paths affect package metadata, public exports, operator/layer/model APIs, backend dispatch, tests, benchmarks, install docs, or environment variables, refresh the skill.
- If package metadata or public entry points changed even on the same commit, refresh the skill.
- If optional backend policy changed for CUDA, ROCm, XPU, NPU, TileLang, FlashKDA, or context parallel, refresh the setup, ops, KDA, and benchmarking references.
