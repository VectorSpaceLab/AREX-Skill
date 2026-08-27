# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T06:43:27Z",
  "repository": {
    "name": "code-review-graph",
    "remote_url": "https://github.com/tirth8205/code-review-graph.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "1a010deed6c283d4aa1e7e949e78fe3a7bcdfbb3",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/code-review-graph.log",
      "skills/disco/",
      "skills/tests/"
    ]
  },
  "packages": [
    {
      "name": "code-review-graph",
      "version": "2.3.7",
      "import_names": ["code_review_graph"]
    }
  ],
  "evidence": {
    "source_roots": ["code_review_graph/"],
    "docs": [
      "README.md",
      "docs/USAGE.md",
      "docs/COMMANDS.md",
      "docs/FEATURES.md",
      "docs/FAQ.md",
      "docs/TROUBLESHOOTING.md",
      "docs/architecture.md",
      "docs/schema.md",
      "docs/CUSTOM_LANGUAGES.md",
      "docs/GITHUB_ACTION.md",
      "docs/REPRODUCING.md",
      "code_review_graph/docs/LLM-OPTIMIZED-REFERENCE.md"
    ],
    "scripts": [
      "scripts/render_pr_comment.py",
      "scripts/diagnose_pypi_connectivity.py",
      "hooks/session-start.sh",
      "action.yml"
    ],
    "tests": ["tests/"],
    "existing_skills": ["skills/build-graph/", "skills/review-delta/", "skills/review-pr/", "skills/explore-codebase/", "skills/debug-issue/", "skills/refactor-safely/", "skills/review-changes/"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, console entry points, MCP tool names, optional extras, or public docs changed, refresh this skill.
- If the current working tree has uncommitted source or docs changes outside generated skill/artifact outputs, refresh after deciding whether those changes are part of the intended package snapshot.
- If the selected scope expands to the separate VS Code extension package, create or extend coverage rather than assuming this Python CLI/MCP skill covers it fully.