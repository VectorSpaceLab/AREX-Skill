# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current commit, dirty state, package/layout baseline, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T07:25:40Z",
  "repository": {
    "name": "InternLM-XComposer",
    "remote_url": "https://github.com/InternLM/InternLM-XComposer.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "0f70c3e3911189de1869396b4017714c31821e3a",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": []
    },
    {
      "name": "share4v",
      "version": "1.0.0",
      "import_names": ["share4v"]
    },
    {
      "name": "dualfocus",
      "version": "1.0.0",
      "import_names": ["dualfocus"]
    }
  ],
  "evidence": {
    "source_roots": [
      "InternLM-XComposer-1.0",
      "InternLM-XComposer-2.0",
      "InternLM-XComposer-2.5-OmniLive/internlm-xcomposer2d5-ol-7b",
      "InternLM-XComposer-2.5-Reward",
      "projects/ShareGPT4V/share4v",
      "projects/DualFocus/dualfocus"
    ],
    "docs": [
      "README.md",
      "README_CN.md",
      "docs/install.md",
      "InternLM-XComposer-1.0/docs/install.md",
      "InternLM-XComposer-2.0/docs/install.md",
      "InternLM-XComposer-2.5-OmniLive/README.md",
      "InternLM-XComposer-2.5-Reward/README.md",
      "projects/ShareGPT4V/README.md",
      "projects/DualFocus/README.md"
    ],
    "examples": [
      "example_code",
      "examples",
      "gradio_demo",
      "InternLM-XComposer-1.0/examples",
      "InternLM-XComposer-2.0/examples",
      "InternLM-XComposer-2.5-OmniLive/examples",
      "projects/ShareGPT4V/examples"
    ],
    "tests": [
      "evaluation",
      "InternLM-XComposer-1.0/evaluation",
      "InternLM-XComposer-2.0/evaluation",
      "InternLM-XComposer-2.5-OmniLive/benchmarks",
      "InternLM-XComposer-2.5-Reward/evaluation",
      "projects/ShareGPT4V/share4v/eval",
      "projects/DualFocus/dualfocus/eval"
    ],
    "configs": [
      "finetune/ds_config_zero2.json",
      "InternLM-XComposer-1.0/finetune/ds_config_zero2.json",
      "InternLM-XComposer-2.0/finetune/ds_config_zero2.json",
      "InternLM-XComposer-2.5-OmniLive/online_demo/Frontend/package.json",
      "projects/ShareGPT4V/pyproject.toml",
      "projects/DualFocus/pyproject.toml"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and refresh it.
- If the working tree becomes clean or dirtier in a materially different way, refresh it.
- If public install pins, entry points, or model APIs change, refresh it.
