# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of LazyLLM. If the current commit, public package metadata, optional dependency groups, CLI dispatcher, or major evidence paths differ from this snapshot, run a repo-skill refresh.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T17:38:51Z",
  "repository": {
    "name": "LazyLLM",
    "remote_url": "https://github.com/LazyAGI/LazyLLM.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "b59fa82bc19c6de3fa550c8084056be7ea03feb8",
    "working_tree": "dirty",
    "dirty_paths": [
      "lazyllm/pyproject.toml",
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "lazyllm",
      "version": "0.7.5",
      "import_names": ["lazyllm"]
    }
  ],
  "python": {
    "requires": ">=3.10,<3.14"
  },
  "evidence": {
    "source_roots": [
      "lazyllm/",
      "csrc/"
    ],
    "docs": [
      "README.md",
      "README.CN.md",
      "docs/en/",
      "docs/zh/",
      "docs/lazyllm-skill/",
      "lazyllm/docs/"
    ],
    "examples": [
      "examples/"
    ],
    "tests": [
      "tests/basic_tests/",
      "tests/advanced_tests/",
      "tests/charge_tests/",
      "tests/engine_tests/",
      "tests/doc_check/",
      "tests/test_cpp_class_decorator.py",
      "tests/test_cpp_proxy_decorator.py"
    ],
    "configs": [
      "pyproject.toml",
      "requirements.txt",
      "tests/requirements.txt",
      "Makefile"
    ],
    "repo_guidance": [
      "lazyllm/AGENTS.md",
      "lazyllm/common/AGENTS.md",
      "lazyllm/components/AGENTS.md",
      "lazyllm/flow/AGENTS.md",
      "lazyllm/module/AGENTS.md",
      "lazyllm/module/llms/onlinemodule/AGENTS.md",
      "lazyllm/tools/AGENTS.md",
      "lazyllm/tools/agent/AGENTS.md",
      "lazyllm/tools/rag/AGENTS.md"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If package name, version, Python range, extras, entry points, CLI commands, or public module names changed, refresh even if the commit is nearby.
- If source files under `lazyllm/`, examples, docs, or behavior tests changed materially, refresh the affected sub-skill.
- `skills/` was also the output area for generated skill and production logs. Do not treat generated skill files alone as evidence that LazyLLM source behavior changed.
- `lazyllm/pyproject.toml` appeared as an untracked generated/duplicated metadata file at snapshot time; compare it with the root `pyproject.toml` before using it as source evidence.

## Extraction Scope Baseline

Included source evidence: public package APIs, CLI dispatcher, LazyLLM docs/examples, repo guidance files, optional dependency declarations, and representative tests for core runtime, modules, flows, RAG, agents/tools, writer/review, and model deployment.

Excluded from runtime dependency: original checkout paths, build/cache output, vendored/generated files, CI-only mechanics, large model/data artifacts, and unsafe provider/GPU/external-service examples unless distilled into this skill's references.
