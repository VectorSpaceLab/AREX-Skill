# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a LaVague checkout. If the current repo commit, dirty state, package versions, public APIs, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T06:00:42Z",
  "repository": {
    "name": "LaVague",
    "remote_url": "https://github.com/lavague-ai/LaVague.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "9024bb832c40291cd012916757f27ef60469b22d",
    "working_tree": "clean-at-source-analysis-before-generated-skills",
    "dirty_paths": []
  },
  "packages": [
    {"name": "lavague", "version": "1.1.19", "import_names": ["lavague"]},
    {"name": "lavague-core", "version": "0.2.35", "import_names": ["lavague.core"]},
    {"name": "lavague-drivers-selenium", "version": "0.2.15", "import_names": ["lavague.drivers.selenium"]},
    {"name": "lavague-drivers-playwright", "version": "0.2.11", "import_names": ["lavague.drivers.playwright"]},
    {"name": "lavague-contexts-openai", "version": "0.2.4", "import_names": ["lavague.contexts.openai"]},
    {"name": "lavague-contexts-cache", "version": "0.0.1", "import_names": ["lavague.contexts.cache"]},
    {"name": "lavague-contexts-anthropic", "version": "0.1.3", "import_names": ["lavague.contexts.anthropic"]},
    {"name": "lavague-contexts-gemini", "version": "0.2.1", "import_names": ["lavague.contexts.gemini"]},
    {"name": "lavague-contexts-fireworks", "version": "0.0.3", "import_names": ["lavague.contexts.fireworks"]},
    {"name": "lavague-retriever-cohere", "version": "0.2.0", "import_names": ["lavague.retrievers.cohere"]},
    {"name": "lavague-gradio", "version": "0.2.8", "import_names": ["lavague.gradio"]},
    {"name": "lavague-server", "version": "0.0.4", "import_names": ["lavague.server"]},
    {"name": "lavague-tests", "version": "0.0.4", "import_names": ["lavague.tests"]},
    {"name": "lavague-qa", "version": "0.0.6", "import_names": ["lavague.qa"]}
  ],
  "evidence": {
    "source_roots": [
      "_lavague/lavague/_bundle",
      "lavague-core/lavague/core",
      "lavague-integrations/contexts",
      "lavague-integrations/drivers",
      "lavague-integrations/retrievers",
      "lavague-gradio/lavague/gradio",
      "lavague-server/lavague/server",
      "lavague-qa/lavague/qa",
      "lavague-tests/lavague/tests"
    ],
    "docs": [
      "README.md",
      "docs/docs/get-started",
      "docs/docs/module-guides",
      "docs/docs/integrations",
      "docs/docs/lavague-qa",
      "docs/docs/learn",
      "docs/docs/use-cases"
    ],
    "examples": ["examples", "examples/knowledge"],
    "tests": ["tests/lavague-core", "lavague-tests/sites"],
    "configs": ["pyproject.toml", "mkdocs.yml", "lavague-tests/sites/*/config.yml"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as potentially stale.
- If package metadata or console entry points changed, refresh even when the commit is the same.
- If the current checkout is dirty in source, docs, examples, integration packages, server, QA, or test-runner paths, refresh or compare those changes before using workflow-specific guidance.
- Generated skill output and review artifacts are not source evidence; do not count them as source dirty paths for staleness decisions.
