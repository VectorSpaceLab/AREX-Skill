# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty source state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T16:37:25Z",
  "repository": {
    "name": "openai-agents-python",
    "remote_url": "https://github.com/openai/openai-agents-python",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "28d2a6c8382992b80421c9179997492e5fc39ce0",
    "working_tree": "clean-source-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "openai-agents",
      "version": "0.17.6",
      "import_names": ["agents"]
    }
  ],
  "evidence": {
    "source_roots": ["src/agents"],
    "docs": [
      "README.md",
      "docs/index.md",
      "docs/quickstart.md",
      "docs/agents.md",
      "docs/running_agents.md",
      "docs/results.md",
      "docs/streaming.md",
      "docs/tools.md",
      "docs/handoffs.md",
      "docs/guardrails.md",
      "docs/human_in_the_loop.md",
      "docs/mcp.md",
      "docs/models/index.md",
      "docs/models/litellm.md",
      "docs/realtime",
      "docs/sandbox_agents.md",
      "docs/sandbox",
      "docs/sessions",
      "docs/tracing.md",
      "docs/usage.md",
      "docs/visualization.md",
      "docs/voice"
    ],
    "examples": [
      "examples/basic",
      "examples/agent_patterns",
      "examples/tools",
      "examples/mcp",
      "examples/hosted_mcp",
      "examples/memory",
      "examples/model_providers",
      "examples/realtime",
      "examples/sandbox",
      "examples/voice",
      "examples/reasoning_content"
    ],
    "tests": [
      "tests/test_agent_runner*.py",
      "tests/test_run*.py",
      "tests/test_run_state.py",
      "tests/test_function_tool*.py",
      "tests/test_guardrails.py",
      "tests/test_handoff*.py",
      "tests/mcp",
      "tests/memory",
      "tests/models",
      "tests/realtime",
      "tests/sandbox",
      "tests/tracing",
      "tests/voice"
    ],
    "configs": ["pyproject.toml", "Makefile", "mkdocs.yml", "AGENTS.md", "PLANS.md", "tests/README.md"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If source files, public docs, examples, tests, package metadata, optional extras, or maintainer policy files changed since this snapshot, run `refresh-repo-skill`.
- Ignore generated DisCo runtime and review outputs when judging whether the original source checkout was dirty for this baseline.
- If `openai-agents` package metadata or public entry points differ from the snapshot even on the same commit, run `refresh-repo-skill`.
