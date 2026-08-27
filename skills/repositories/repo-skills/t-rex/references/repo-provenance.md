# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T09:15:42Z",
  "repository": {
    "name": "T-Rex",
    "remote_url": "https://github.com/IDEA-Research/T-Rex.git",
    "vcs": "git",
    "branch": "trex2",
    "tag": null,
    "commit": "e5fd60fb94cd4abb29d5ec180a616e2e0fb36c9f",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "trex",
      "version": "1.0",
      "source_version_file": "v1.0",
      "import_names": ["trex"]
    }
  ],
  "evidence": {
    "source_roots": ["trex/"],
    "docs": ["README.md", "LICENSE"],
    "examples": ["demo_examples/", "gradio_demo.py"],
    "assets": ["assets/trex2_api_examples/", "assets/trex2/"],
    "package_metadata": ["setup.py", "requirements.txt"],
    "tests": [],
    "existing_repo_skills": ["skills/T-Rex.log"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree's source/package/docs/example dirty paths differ from this snapshot, run `refresh-repo-skill`.
- Ignore dirty paths that are only generated skill artifacts when comparing a checkout immediately after this creation run.
- If package metadata, public imports, cloud API wrapper methods, demo scripts, dependency pins, or Gradio behavior changed even on the same commit, run `refresh-repo-skill`.

## Evidence notes

- The package metadata reports distribution version `1.0`; the source version file contains `v1.0`.
- The selected skill scope covers the cloud API wrapper, prompt/embedding workflows, visualization, and optional Gradio demo. It does not cover local model training or offline model inference.
- Live cloud examples require external credentials and network access, so public source examples are treated as workflow evidence and optional native verification candidates rather than mandatory offline tests.
