# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a LangBot checkout.
If the current commit, dirty state, package version, entry points, or evidence
layout differ materially from this snapshot, refresh the repo skill before using
it for high-risk changes.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T00:00:00Z",
  "repository": {
    "name": "LangBot",
    "remote_url": "https://github.com/langbot-app/LangBot",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "90f3d880e504d638f8cde637138c544e1a481948",
    "working_tree": "dirty",
    "dirty_paths": ["skills/LangBot.log"]
  },
  "packages": [
    {"name": "langbot", "version": "4.10.7", "import_names": ["langbot"]},
    {"name": "langbot-plugin", "version": "0.5.0", "import_names": ["langbot_plugin"]}
  ],
  "entry_points": {"console_scripts": ["langbot = langbot.__main__:main"]},
  "evidence": {
    "source_roots": ["src/langbot"],
    "source_support": ["main.py", "pyproject.toml", "uv.lock", "pytest.ini", "Makefile"],
    "docs": ["README.md", "ARCHITECTURE.md", "AGENTS.md", "docs"],
    "examples": ["examples/http-bot", "examples/web-page-bot"],
    "tests": ["tests", "web/tests"],
    "configs": ["src/langbot/templates/config.yaml", "src/langbot/templates/metadata"],
    "scripts": ["scripts", "run_tests.sh", "docker"],
    "existing_repo_skills": ["skills/skills", "skills/README.md", "skills/AGENTS.md"]
  },
  "verification_baseline": {
    "metadata": "langbot 4.10.7 and langbot-plugin 0.5.0 metadata verified during skill creation",
    "pip_check": "passed",
    "imports": [
      "langbot", "langbot.__main__", "langbot.pkg.core.app",
      "langbot.pkg.api.mcp.server", "langbot.pkg.pipeline.pipelinemgr",
      "langbot.pkg.platform.botmgr", "langbot.pkg.provider.tools.toolmgr",
      "langbot.pkg.plugin.connector", "langbot.pkg.box.service",
      "langbot.pkg.persistence.mgr", "langbot.pkg.rag.knowledge.kbmgr"
    ],
    "cli_help": "langbot --help passed"
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as
  potentially stale.
- If package metadata, console entry points, required Python, or the pinned
  `langbot-plugin` SDK revision changes, refresh the skill.
- If the main source layout, route groups, MCP tool surface, migration layout,
  or in-repo skills catalog changes, refresh the affected sub-skills.
- Ignore generated runtime skill files themselves when comparing dirty state;
  the dirty path recorded above was the source checkout state before this skill
  was generated.
