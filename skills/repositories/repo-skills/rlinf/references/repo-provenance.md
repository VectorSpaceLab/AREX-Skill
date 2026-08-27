# Repository Provenance

## Purpose

Read this before deciding whether this RLinf repo skill is current for a checkout of the repository. If the current repo commit, dirty state, package metadata, major examples/configs, or public APIs differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T03:34:19Z",
  "repository": {
    "name": "RLinf",
    "remote_url": "https://github.com/RLinf/RLinf.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "9ad44393d15b0e93461d7415591110678ae17ef6",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "rlinf",
      "version": "0.4.0",
      "import_names": ["rlinf"]
    }
  ],
  "evidence": {
    "source_roots": ["rlinf"],
    "docs": ["README.md", "README.zh-CN.md", "docs/source-en/rst_source"],
    "examples": ["examples/embodiment", "examples/reasoning", "examples/agent", "examples/sft", "examples/reward", "examples/offline_rl"],
    "evaluations": ["evaluations"],
    "tests": ["tests/unit_tests", "tests/e2e_tests", "tests/parity_tests"],
    "configs": ["examples/embodiment/config", "examples/reasoning", "examples/sft/config", "examples/offline_rl/config", "evaluations"],
    "scripts_and_tools": ["requirements", "ray_utils", "docker", "toolkits"],
    "agent_guidance": ["AGENTS.md", "CONTRIBUTING.md", ".cursor/skills", ".claude/skills", ".codex/skills"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as potentially stale.
- If the current checkout has non-generated source, config, docs, example, requirements, scheduler, model, env, runner, worker, or toolkit changes not reflected here, refresh the skill.
- If `pyproject.toml` changes the `rlinf` version, dependencies, extras, supported Python version, or package discovery, refresh the skill.
- If `rlinf/config.py`, environment/model registries, scheduler placement APIs, examples, or docs change, refresh the affected sub-skills.
