# Repository Provenance

Read this before deciding whether the ROSA skill is current for a checkout. If
the commit, dirty paths, package version, public entry points, or major evidence
paths differ, run the repository-skill refresh workflow.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T17:50:57Z",
  "repository": {
    "name": "rosa",
    "remote_url": "https://github.com/nasa-jpl/rosa.git",
    "vcs": "git",
    "branch": "main",
    "tag": "v1.0.10",
    "commit": "e7e53754bed673e2ce36d1fa311e04e51bfbacad",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "jpl-rosa",
      "version": "1.0.10",
      "import_names": ["rosa"]
    }
  ],
  "evidence": {
    "source_roots": ["src/rosa"],
    "docs": ["README.md", "TESTING.md", "CHANGELOG.md"],
    "examples": ["demo.sh", "src/turtle_agent"],
    "tests": ["tests/test_rosa"],
    "configs": ["pyproject.toml", "setup.py", ".github/workflows/ci.yml"]
  }
}
```

The checkout was dirty only because the generated skill and review artifacts
were being produced under `skills/`; the source commit and package version are
otherwise the pinned baseline above. The example/demo paths are provenance
inputs only. The runtime skill contains distilled guidance and does not require
the original checkout, Docker demo, GUI, or test files.

## Refresh check

- Compare `git rev-parse HEAD` with the pinned commit.
- Compare the package metadata and public exports (`ROSA`,
  `RobotSystemPrompts`, `ChatModel`) with the snapshot.
- Check whether `src/rosa/rosa.py`, `src/rosa/prompts.py`, `src/rosa/tools/ros1.py`,
  `src/rosa/tools/ros2.py`, and `src/rosa/tools/__init__.py` changed.
- If the dirty state or relative evidence paths materially differ, refresh
  before relying on this operating graph.
