# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
OpenMOSS/MOSS repository. If the current repo commit, dirty state, package
layout, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-12T16:30:00Z",
  "repository": {
    "name": "MOSS",
    "remote_url": "https://github.com/OpenMOSS/MOSS.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "d2ef690e59e0ab5f796db98f168d561c232a4b70",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": [
        "models",
        "models_jittor",
        "moss_inference",
        "finetune_moss"
      ],
      "notes": "The repository has no pyproject.toml, setup.py, or setup.cfg package metadata; local usage imports source modules or Hugging Face remote code."
    }
  ],
  "evidence": {
    "source_roots": [
      "models",
      "models_jittor"
    ],
    "docs": [
      "README.md",
      "README_en.md",
      "SFT_data/README.md"
    ],
    "examples": [
      "examples"
    ],
    "scripts": [
      "moss_inference.py",
      "moss_cli_demo.py",
      "moss_cli_demo_jittor.py",
      "moss_api_demo.py",
      "moss_web_demo_gradio.py",
      "moss_web_demo_streamlit.py",
      "finetune_moss.py",
      "utils.py"
    ],
    "configs": [
      "configs/sft.yaml",
      "requirements.txt",
      "meta_instruction.txt"
    ],
    "data_schema_samples": [
      "SFT_data/conversations/conversation_without_plugins",
      "SFT_data/conversations/conversation_with_plugins",
      "SFT_data/user_prompts"
    ],
    "licenses": [
      "LICENSE",
      "MODEL_LICENSE",
      "DATA_LICENSE",
      "agreements"
    ],
    "tests": []
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If current source files under `models/`, `models_jittor/`, runtime scripts,
  `configs/`, or `SFT_data/README.md` changed, refresh this skill.
- If MOSS gains conventional package metadata, new public checkpoint families,
  changed prompt markers, new service APIs, or new SFT schema rules, refresh.
- Ignore differences limited to generated `skills/` artifacts unless refreshing
  or verifying the generated skill itself.
