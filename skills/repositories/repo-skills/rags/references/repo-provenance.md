# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
RAGs repository. If the current repo commit, dirty state, package metadata, or
major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T19:21:50Z",
  "repository": {
    "name": "rags",
    "remote_url": "https://github.com/run-llama/rags.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "4bec27023950c078fe0d559e1720d757d0024c93",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "rags",
      "version": "0.0.5",
      "import_names": ["core", "st_utils"],
      "package_install_note": "Current snapshot is app-style; root package install fails because no import package named rags exists."
    }
  ],
  "evidence": {
    "source_roots": [
      "core",
      "st_utils.py",
      "1_🏠_Home.py",
      "pages/2_⚙️_RAG_Config.py",
      "pages/3_🤖_Generated_RAG_Agent.py"
    ],
    "docs": ["README.md"],
    "examples": ["pg_essay.txt"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "requirements.txt", "Makefile", ".github/workflows/lint.yml"],
    "existing_skills_or_artifacts": ["skills/rags.log"]
  },
  "verification_baseline": {
    "python": "3.10.20",
    "dependencies": {
      "streamlit": "1.28.0",
      "llama-index": "0.9.7",
      "llama-hub": "0.0.44",
      "langchain": "0.0.305",
      "pypdf": "3.17.1"
    },
    "required_backend": "any/cpu",
    "optional_unverified": ["external provider calls", "URL downloads", "web search", "beta multimodal torch/CLIP runtime"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree is clean or has dirty paths other than the
  generated `skills/` artifacts listed above, compare source changes before
  relying on this skill.
- If package metadata changes to add a real `rags` import package, update the
  install guidance and root troubleshooting notes.
- If Streamlit pages, cache layout, builder methods, model resolver behavior,
  or supported dependencies change, refresh the matching sub-skill.
