# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T04:40:01Z",
  "repository": {
    "name": "gptme",
    "remote_url": "https://github.com/gptme/gptme.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "66057c6e898e0fe3df05bb8cc648db7df87935cf",
    "working_tree": "clean-before-generated-skill-artifacts",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "gptme",
      "version": "0.32.1",
      "import_names": ["gptme"]
    },
    {
      "name": "gptme-acp",
      "version": null,
      "import_names": ["gptme_acp"]
    }
  ],
  "evidence": {
    "source_roots": ["gptme", "packages/gptme-acp/gptme_acp"],
    "docs": [
      "README.md",
      "AGENTS.md",
      "docs/getting-started.rst",
      "docs/usage.rst",
      "docs/cli.rst",
      "docs/commands.rst",
      "docs/config.rst",
      "docs/providers.rst",
      "docs/custom-providers.rst",
      "docs/system-dependencies.rst",
      "docs/tools.rst",
      "docs/browser.md",
      "docs/custom_tool.rst",
      "docs/plugins.rst",
      "docs/hooks.rst",
      "docs/mcp.rst",
      "docs/skills.rst",
      "docs/lessons.rst",
      "docs/server.rst",
      "docs/api.rst",
      "docs/tui.rst",
      "docs/acp.rst",
      "docs/agents.rst",
      "docs/automation.rst",
      "docs/evals.rst",
      "docs/contributing.rst",
      "docs/pr-lifecycle.rst",
      "docs/arewetiny.rst"
    ],
    "interfaces": ["webui", "packages/gptme-acp"],
    "tests": ["tests", "gptme/hooks/tests", "webui/e2e"],
    "configs": ["pyproject.toml", "poetry.lock", "Makefile", "gptme.toml", "docker-compose.yml", "webui/package.json", "webui/AGENTS.md"],
    "scripts": ["scripts"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` in a target checkout differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the source checkout has meaningful uncommitted changes in package metadata, docs, interfaces, or selected source roots, refresh before relying on exact signatures or commands.
- If `pyproject.toml` entry points/extras or package version changed, refresh.
- If server route families, Web UI message metadata, tool/plugin/hook APIs, eval result schemas, or maintainer policy changed, refresh.

## Notes

The clean working-tree state above was captured before generated runtime and review artifacts were written. Those generated outputs are products of this construction workflow, not upstream source dirtiness.
