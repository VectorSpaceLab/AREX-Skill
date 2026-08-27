# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a Browser Use checkout. If the current repo commit, dirty state, package version, public APIs, entry points, docs, examples, or major evidence paths differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "browser-use",
    "remote_url": "https://github.com/browser-use/browser-use",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "48c3c882ac5f5557c011cb0c8edfc53962da5899",
    "working_tree": "dirty",
    "dirty_paths": [
      "generated DisCo runtime skill directory",
      "generated DisCo review artifact directory"
    ]
  },
  "packages": [
    {
      "name": "browser-use",
      "version": "0.13.2",
      "import_names": ["browser_use"]
    }
  ],
  "entry_points": {
    "console_scripts": ["browser-use", "browseruse", "bu", "browser", "browser-use-tui"]
  },
  "evidence": {
    "source_roots": [
      "browser_use/agent/",
      "browser_use/beta/",
      "browser_use/browser/",
      "browser_use/actor/",
      "browser_use/dom/",
      "browser_use/tools/",
      "browser_use/controller/",
      "browser_use/filesystem/",
      "browser_use/llm/",
      "browser_use/tokens/",
      "browser_use/skill_cli/",
      "browser_use/sandbox/",
      "browser_use/sync/",
      "browser_use/mcp/",
      "browser_use/skills/",
      "browser_use/telemetry/"
    ],
    "docs": [
      "README.md",
      "browser_use/README.md",
      "CLOUD.md",
      "BETA_AGENT_INTEGRATION_FEATURES.md",
      "AGENTS.md",
      "CLAUDE.md",
      "browser_use/skill_cli/README.md"
    ],
    "examples": [
      "examples/getting_started/",
      "examples/features/",
      "examples/browser/",
      "examples/custom-functions/",
      "examples/cloud/",
      "examples/sandbox/",
      "examples/models/",
      "examples/integrations/",
      "examples/file_system/",
      "examples/ui/",
      "examples/use-cases/",
      "examples/beta_agent/"
    ],
    "tests": [
      "tests/ci/",
      "tests/agent_tasks/"
    ],
    "existing_repo_skills": [
      "skills/browser-use/",
      "skills/open-source/",
      "skills/cloud/",
      "skills/remote-browser/",
      "skills/qa/",
      "skills/x402/"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-skill-from-repo`.
- If the current working tree dirty paths differ materially from this snapshot, run `refresh-skill-from-repo`.
- If `pyproject.toml` changes the package version, dependencies, extras, or console scripts, refresh.
- If public signatures for `Agent`, `Browser`, `BrowserProfile`, `Tools`, `ActionResult`, `ChatBrowserUse`, sandbox, MCP, or CLI commands change, refresh.
