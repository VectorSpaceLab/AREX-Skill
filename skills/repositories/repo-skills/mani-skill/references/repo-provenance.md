# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the ManiSkill repository. If the current repo commit, dirty state, package version, public APIs, examples, docs, or dependency metadata differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T19:16:03Z",
  "repository": {
    "name": "ManiSkill",
    "remote_url": "https://github.com/mani-skill/ManiSkill.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "The only visible dirty path during generation was repo-local skill/test/log output under skills/. Source files used as evidence were not modified before skill generation."
  },
  "packages": [
    {
      "name": "mani_skill",
      "version": "3.0.1",
      "import_names": ["mani_skill"]
    }
  ],
  "runtime_dependencies_observed": {
    "python": "3.11",
    "torch": "2.13.0+cu130",
    "sapien": "3.0.3",
    "gymnasium": "1.3.0",
    "mplib": "0.1.1",
    "tyro": "1.0.15",
    "h5py": "3.16.0",
    "pandas": "3.0.5"
  },
  "evidence": {
    "package_metadata": ["setup.py", "pyproject.toml"],
    "source_roots": ["mani_skill"],
    "docs": ["README.md", "docs/source/user_guide"],
    "examples": ["mani_skill/examples", "examples/tutorials", "examples/baselines"],
    "scripts": ["scripts/data_generation", "scripts/mesh"],
    "tests": ["tests"],
    "native_candidate_summary": "CPU package import and PickCube-v1 no-render reset/step passed; optional no-render PhysX CUDA smoke passed; Vulkan rendering and training-scale baseline execution were not required for generation."
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, public environment registration, CLI/module help, trajectory APIs, wrappers, or custom-task templates changed, run `refresh-repo-skill` even on the same commit.
- If the current working tree has source-code changes outside generated skill/test artifacts, run `refresh-repo-skill`.
- If ManiSkill moves major baseline, dataset, or task authoring surfaces into different packages or extras, refresh the skill and rerun verification.
