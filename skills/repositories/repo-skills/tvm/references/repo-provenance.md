# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Apache
TVM. If the current repo commit, dirty state, package metadata, or major evidence
paths differ from this snapshot, run a repo-skill refresh.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T19:41:56Z",
  "repository": {
    "name": "apache-tvm",
    "remote_url": "https://github.com/apache/tvm.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "bb9bc20a8294fb19a2a40f029fe57baa546a8206",
    "working_tree": "dirty-generated-artifacts-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "apache-tvm",
      "version": "0.26.dev0",
      "import_names": ["tvm"]
    },
    {
      "name": "apache-tvm-ffi",
      "version": "0.1.13.post2",
      "import_names": ["tvm_ffi"]
    }
  ],
  "evidence": {
    "source_roots": ["python/tvm", "src", "include/tvm"],
    "docs": [
      "README.md",
      "docs/install",
      "docs/get_started",
      "docs/how_to/tutorials",
      "docs/tirx",
      "docs/reference/api/python"
    ],
    "tests": [
      "tests/python/all-platform-minimal-test",
      "tests/python/tirx",
      "tests/python/s_tir",
      "tests/python/runtime",
      "tests/python/contrib/test_rpc_proxy.py",
      "tests/python/contrib/test_rpc_tracker.py"
    ],
    "configs": ["pyproject.toml", "CMakeLists.txt", "cmake/config.cmake"],
    "repo_local_agent_guidance": ["AGENTS.md", ".agents/skills", ".agents/scripts"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat the skill as
  potentially stale.
- If tracked source files, package metadata, CMake options, public Python API
  modules, TIRx docs/tests, S-TIR/meta-schedule docs/tests, or RPC docs/tests
  changed, refresh the skill even if the checkout is on a nearby commit.
- If the only dirty paths are generated skill artifacts or local build outputs,
  they do not by themselves mean the source evidence changed.
- If a task requires a backend not verified by this skill, refresh or extend the
  skill with that backend-specific evidence before relying on it.
