# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
`wkentaro/labelme`. If the current repo commit, dirty state, package version, or
major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T16:40:06Z",
  "repository": {
    "name": "labelme",
    "remote_url": "https://github.com/wkentaro/labelme.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "be8b2a05b419660caa62379e35feed5141c13eeb",
    "working_tree": "dirty-generated-skills-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "labelme",
      "version": "0.1.dev1+gbe8b2a05b",
      "import_names": ["labelme"]
    }
  ],
  "evidence": {
    "source_roots": ["labelme/"],
    "docs": ["README.md", "CONTEXT.md", "docs/adr/", "docs/agents/"],
    "examples": ["examples/"],
    "tests": ["tests/unit/", "tests/e2e/", "tests/data/"],
    "configs": ["pyproject.toml", "Makefile", ".github/workflows/test.yml", "labelme/_config/default_config.yaml"],
    "tools": ["tools/release_notes.py", "tools/update_translate.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree has non-generated changes that are not represented
  above, refresh before relying on workflow details or test routing.
- If package metadata, the `labelme` console entry point, the Annotation File
  schema, AI model options, or conversion example behavior changed, refresh even
  on the same commit.
- This skill was generated from a checkout whose dirty state was limited to
  generated `skills/` artifacts; do not interpret those artifacts as upstream
  labelme source evidence.
