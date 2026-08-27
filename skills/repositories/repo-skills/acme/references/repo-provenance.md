# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an Acme checkout. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-29T15:30:00Z",
  "repository": {
    "name": "acme",
    "remote_url": "https://github.com/google-deepmind/acme.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "01beece5808fb7337a3980b19359ba0ae170331f",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "dm-acme",
      "version": "0.4.1",
      "import_names": ["acme"]
    }
  ],
  "evidence": {
    "source_roots": ["acme"],
    "docs": ["README.md", "docs/user/overview.md", "docs/user/components.md", "docs/user/agents.md", "docs/faq.md"],
    "examples": ["examples"],
    "tests": ["acme/**/*_test.py"],
    "configs": ["setup.py", "docs/requirements.txt"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, optional extras, public agent families, or experiment APIs changed even on the same commit, run `refresh-repo-skill`.
- If the current checkout has source changes outside generated `skills/` artifacts, compare affected paths with the evidence list and refresh when they touch public APIs, docs, examples, tests, or dependencies.
