# Repository Provenance

## Purpose

Read this before deciding whether this `missingno` repo skill is current for a
checkout. If the current repository commit, tag, dirty state, package metadata,
or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T04:31:25Z",
  "repository": {
    "name": "missingno",
    "remote_url": "https://github.com/ResidentMario/missingno.git",
    "vcs": "git",
    "branch": "master",
    "tag": "0.5.2",
    "commit": "570fa089ba6338e02342ed990bbc1b0bedc54314",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "missingno",
      "version": "0.5.2",
      "import_names": ["missingno"]
    }
  ],
  "evidence": {
    "source_roots": ["missingno/"],
    "docs": ["README.md", "CONFIGURATION.md", "CONTRIBUTING.md"],
    "examples": ["README.md quickstart snippets"],
    "tests": ["tests/test_util.py", "tests/test_viz.py"],
    "configs": ["setup.py", "MANIFEST.in"],
    "context": ["paper.md", "paper.bib"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If package version, public exports, setup dependencies, or documented plot
  parameters change, refresh this skill even if the commit is otherwise known.
- The dirty state above reflects repo-local `skills/` production artifacts;
  source package, docs, and tests were used as evidence from the recorded
  commit/tag. If source files under `missingno/`, root docs, or `tests/` are
  dirty in a future checkout, refresh before relying on API details.
- This skill intentionally avoids depending on any original checkout path at
  runtime. Evidence paths above are staleness anchors, not files future agents
  must open to use the skill.
