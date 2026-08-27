# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of InfiniteYou. If the current repo commit, dirty state, package/source layout, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T14:44:28Z",
  "repository": {
    "name": "InfiniteYou",
    "remote_url": "https://github.com/bytedance/InfiniteYou.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "aaa6ea5f75ba2ff58b9025fa7df45e4a139ed717",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["pipelines"]
    }
  ],
  "evidence": {
    "source_roots": ["pipelines/"],
    "docs": ["README.md", "LICENSE"],
    "examples": ["assets/examples/"],
    "tests": [],
    "configs": [],
    "scripts": ["test.py", "app.py"],
    "dependencies": ["requirements.txt"]
  },
  "construction_notes": {
    "package_layout": "source-only checkout without pyproject.toml or setup.py; generated skill bundles runtime/pipelines for self-contained operation",
    "required_backend": "cuda for generation",
    "model_artifacts": "external model files and access are required for native generation but are not bundled"
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source changes outside generated skill/test artifacts, refresh before relying on API or command details.
- If the repository adds packaging metadata, training/evaluation code, new model variants, new CLI flags, or a changed `pipelines/` API, refresh the skill.
- If dependency pins change, re-run the environment checker and refresh references that mention versions or backend behavior.
