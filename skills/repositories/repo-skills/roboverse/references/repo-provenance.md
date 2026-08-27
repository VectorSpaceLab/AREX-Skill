# Repository Provenance

Read this before treating the skill as current for a checkout. If the commit,
dirty state, package metadata, or major evidence paths differ, use a refresh
workflow before relying on detailed API claims.

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T12:00:00Z",
  "repository": {
    "name": "RoboVerse",
    "remote_url": "https://github.com/RoboVerseOrg/RoboVerse.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "e9b5c6efeb665052edeb934fc3172df8b9d3c9d7",
    "working_tree": "dirty-from-generated-skill-and-review-artifacts",
    "dirty_paths": ["skills/disco/roboverse", "skills/tests/roboverse"]
  },
  "packages": [
    {
      "name": "roboverse-py",
      "version": "1.0.0b0",
      "import_names": ["roboverse_pack", "roboverse_learn"]
    },
    {
      "name": "metasim",
      "version": "0.2.0-at-inspection-time",
      "import_names": ["metasim"]
    }
  ],
  "evidence": {
    "source_roots": ["roboverse_pack", "roboverse_learn", "generation"],
    "docs": ["README.md", "AGENTS.md", "docs/source", "CONTRIBUTING.md", "ROADMAP.md"],
    "examples": ["get_started", "scripts", "tools"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "metasim.toml"]
  }
}
```

## Refresh checks

- Compare the current Git commit with the recorded commit.
- Compare package version and MetaSim public API/entry-point behavior.
- Recheck the task, robot, learning, and integration directories when they
  change; generated/vendor assets and optional backends have intentionally
  limited coverage here.
- Review the artifact reports alongside this runtime tree for the exact native
  cases and backend limits that were verified.
