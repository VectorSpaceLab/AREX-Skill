# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the NVIDIA Agent Skills catalog. If the current checkout differs materially from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T16:38:10Z",
  "repository": {
    "name": "NVIDIA Agent Skills catalog",
    "remote_url": "https://github.com/NVIDIA/skills.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "20bb6aaea832ba254dca639c5e8cbfb3e6de0baa",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/skills.log"
    ]
  },
  "packages": [],
  "evidence": {
    "source_roots": ["components.d", "plugins.d", "skills"],
    "docs": [
      "README.md",
      "docs",
      "skills/README.md",
      "components.d/README.md",
      "plugins.d/README.md",
      "plugins/README.md"
    ],
    "examples": [
      "skills/nvidia-skill-finder",
      "skills/skill-card-generator",
      "plugins/nvidia-skills"
    ],
    "tests": [
      ".github/scripts/marketplace/test_generate_skill_metadata.py",
      ".github/workflows"
    ],
    "configs": [
      "components.d",
      "plugins.d",
      "catalog-exceptions.yml",
      ".github/scripts/manual-components.yml",
      "fern/docs.yml",
      "skills.sh.json",
      "benchmarks.json"
    ],
    "scripts": [
      ".github/scripts/build-plugins.py",
      ".github/scripts/build-plugins.sh",
      ".github/scripts/prune-orphans.sh",
      ".github/scripts/regenerate-readme.sh",
      ".github/scripts/marketplace/generate-skill-metadata.py",
      ".github/scripts/aggregate_benchmarks.py",
      ".github/scripts/verify_content_integrity.py",
      ".github/scripts/version-plugins.py"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has different dirty paths, refresh or review the changed files before relying on this skill.
- If component registration, plugin packaging, metadata generation, signature enforcement, or publication artifact rules changed, refresh this skill even on the same commit.
