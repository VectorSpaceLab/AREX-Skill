# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a SkyPilot checkout. If the current repo commit, dirty state, package version, CLI/API surfaces, YAML schema, docs, examples, or dependency metadata differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T19:07:50Z",
  "repository": {
    "name": "skypilot",
    "remote_url": "https://github.com/skypilot-org/skypilot",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "aea76fdbcb8d8788c02eb29b342ef1a86303b19e",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_state_note": "The source checkout was clean before this generated skill was written. The listed dirty path is the generated DisCo output tree."
  },
  "packages": [
    {
      "name": "skypilot",
      "version": "1.0.0-dev0",
      "import_names": ["sky", "sky_templates"],
      "console_scripts": ["sky"]
    }
  ],
  "evidence": {
    "source_roots": ["sky", "sky_templates"],
    "packaging": ["pyproject.toml", "sky/setup_files/setup.py", "sky/setup_files/dependencies.py", "requirements-dev.txt"],
    "docs": ["README.md", "CONTRIBUTING.md", "AGENTS.md", "docs", "agent/skills/skypilot"],
    "examples": ["examples", "llm"],
    "tests": ["tests/unit_tests", "tests/test_yamls", "tests/skyserve", "tests/test_job_groups", "tests/smoke_tests"],
    "configs_and_templates": ["sky/templates", "sky/schemas/proto", "charts", "Dockerfile", "Dockerfile_k8s", "Dockerfile_k8s_gpu"],
    "generated_or_excluded": ["sky/schemas/generated", "build outputs", "cache directories", "credentialed or cloud-launching native tests"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If public CLI flags, SDK signatures, YAML fields, SkyServe service schema, managed-job behavior, storage/provider semantics, or API server versioning changed, refresh even on the same commit.
- If the current checkout has dirty source paths outside generated skill artifacts, compare them with the evidence map and refresh when they affect user-facing behavior.
- If package metadata, optional extras, supported Python versions, or the `sky` console entry point changed, refresh before trusting install or troubleshooting guidance.
