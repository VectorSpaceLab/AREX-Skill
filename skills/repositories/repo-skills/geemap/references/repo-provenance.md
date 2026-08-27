# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public APIs, optional extras, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T13:49:06Z",
  "repository": {
    "name": "geemap",
    "remote_url": "https://github.com/gee-community/geemap.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "6c0534697deabb1fd2cbdc2c47234ed93d3c57cc",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "geemap",
      "version": "0.38.3.post0",
      "import_names": ["geemap"]
    }
  ],
  "evidence": {
    "source_roots": ["geemap"],
    "docs": ["README.md", "docs"],
    "examples": ["examples", "docs/notebooks", "tutorials"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "environment.yml", "package.json", "mkdocs.yml"],
    "scripts": ["scripts", "examples/python", "examples/javascripts"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata such as Python version, optional extras, console entry points, or public dependencies change, refresh the skill.
- If `geemap.Map`, conversion/export helpers, timelapse APIs, chart/cartoee APIs, ML conversion APIs, or optional AI/backend modules change, refresh the affected sub-skills.
- If docs remove or add major notebook workflows, optional backends, or authentication requirements, refresh the routing metadata and references.
- A dirty path limited to `skills/` indicates this generated skill was written inside the checkout; compare source package paths separately when evaluating code staleness.
