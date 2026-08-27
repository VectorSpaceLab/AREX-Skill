# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "verl",
    "remote_url": "https://github.com/volcengine/verl",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "8a694930275061f52ebd538c906ef8819af56dbd",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "verl",
      "version": "0.9.0.dev0",
      "import_names": [
        "verl"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "verl"
    ],
    "docs": [
      "README.md",
      "docs"
    ],
    "examples": [
      "examples"
    ],
    "tests": [
      "tests"
    ],
    "scripts": [
      "scripts"
    ],
    "configs": [
      "verl/trainer/config",
      "pyproject.toml",
      "setup.py",
      "requirements.txt",
      "requirements-npu.txt",
      "requirements-test.txt"
    ],
    "contributor_guidance": [
      "AGENTS.md",
      "CONTRIBUTING.md",
      "docs/contributing/editing-agent-instructions.md"
    ]
  },
  "generation_scope": {
    "included": [
      "verl/",
      "README.md",
      "docs/",
      "examples/",
      "tests/",
      "scripts/",
      "pyproject.toml",
      "setup.py",
      "requirements*.txt",
      "AGENTS.md",
      "CONTRIBUTING.md"
    ],
    "excluded": [
      ".git/",
      "cache/build/dist outputs",
      "docker/ as runtime dependency",
      "recipe/ as primary extraction source",
      "GPU/NPU/large-cluster native runs as executable checks"
    ],
    "decision_mode": "agent-decide"
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-skill-from-repo`.
- If the working tree dirty paths differ materially from `dirty_paths`, refresh before relying on source-specific claims.
- If package metadata, extras, training config files, rollout/tool APIs, examples, docs, or public test layouts changed, refresh even on the same commit.
- If backend support changed for vLLM, SGLang, Megatron, TensorRT-LLM, ROCm, or NPU stacks, refresh the setup, rollout, and training sub-skills together.
