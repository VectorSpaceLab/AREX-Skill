# Repository Provenance

Read this before deciding whether the operating skill is current for a checkout
of OWL. If the commit, dirty state, package metadata, or major evidence paths
differ, run a repo-skill refresh rather than trusting stale API claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T06:52:19Z",
  "repository": {
    "name": "owl",
    "remote_url": "https://github.com/camel-ai/owl.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "fa5c0b4c3d31217e53fef0b4889f89152b0ecfe6",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "owl",
      "version": "0.0.1",
      "import_names": ["owl", "owl.utils"]
    },
    {
      "name": "camel-ai",
      "version": "0.2.84",
      "import_names": ["camel"]
    }
  ],
  "evidence": {
    "source_roots": ["owl", "owl/utils"],
    "docs": ["README.md", "README_zh.md", "README_ja.md", ".container/DOCKER_README_en.md"],
    "examples": ["examples"],
    "tests": [],
    "configs": ["pyproject.toml", "requirements.txt", "owl/.env_template", ".container/docker-compose.yml", ".container/Dockerfile"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the commit above, treat this skill as
  potentially stale and refresh it.
- If the current working tree is dirty or the recorded dirty paths differ,
  refresh before relying on the generated routes.
- If public exports, provider examples, UI module names, dependencies, or
  Docker layout change, refresh even when the commit appears unchanged.
