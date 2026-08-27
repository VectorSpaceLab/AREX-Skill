# Repository Provenance

## Purpose

Read this before deciding whether the skill matches a checkout of Chinese-LLaMA-Alpaca. If the commit, dirty state, or public evidence paths differ materially, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T00:00:00Z",
  "repository": {
    "name": "Chinese-LLaMA-Alpaca",
    "remote_url": "https://github.com/ymcui/Chinese-LLaMA-Alpaca.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "5b8bb552e8b738da0f19a8e2cedf6db6b5c3fd14",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/Chinese-LLaMA-Alpaca.log",
      "skills/disco/chinese-llama-alpaca/**",
      "skills/tests/chinese-llama-alpaca/**"
    ]
  },
  "packages": [],
  "evidence": {
    "source_roots": ["scripts", "data", "examples"],
    "docs": ["README.md", "README_EN.md", "SHA256.md", "scripts/README.md", "data/README.md", "examples/README.md", "notebooks/README.md"],
    "examples": ["examples/q4_7b-13b", "examples/q8_7b-13b-p7b", "examples/q8_13b-p7b-p13b", "examples/f16-p7b-p13b-33b"],
    "tests": [],
    "configs": ["requirements.txt", "scripts/training/ds_zero2_no_offload.json"]
  }
}
```

## Refresh Check

- If the repo commit changes, refresh the skill.
- If the checkout is clean but this snapshot says dirty, or the dirty paths no longer resemble the generated skill files and log, refresh the skill.
- If the public script list changes, especially in `scripts/`, refresh the skill.
- If the pinned base requirements change, refresh the skill.
- If the repository gains a real installable Python package or public entry points, refresh the skill to record the distribution and import names.
