# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an OpenCLIP checkout. If the current repository commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-23T00:00:00Z",
  "repository": {
    "name": "open_clip",
    "remote_url": "https://github.com/mlfoundations/open_clip",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "0947af57f297b31a5012459846b7d491529d034c",
    "working_tree": "dirty-generated-skill-artifacts",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "open_clip_torch",
      "version": "4.2.0.dev0",
      "import_names": ["open_clip", "open_clip_train"]
    }
  ],
  "evidence": {
    "source_roots": ["src/open_clip", "src/open_clip/audio", "src/open_clip_train"],
    "docs": ["README.md", "HISTORY.md", "docs/PRETRAINED.md", "docs/LOW_ACC.md", "docs/clipa.md", "docs/datacomp_models.md"],
    "scripts": ["scripts", "docs/script_examples"],
    "tests": ["tests"],
    "configs": ["src/open_clip/model_configs", "pyproject.toml", "requirements.txt", "requirements-training.txt", "requirements-test.txt"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If the current dirty paths differ from the generated-skill-only dirty state above, inspect whether public APIs, docs, examples, configs, or tests changed.
- If `open_clip.__version__`, `open_clip.list_models()`, `open_clip.list_pretrained()`, training parser options, or model config names changed, refresh the relevant sub-skills.
- If audio, NaFlex, GenLIP/GenLAP, training task wrappers, checkpoint conversion, or zero-shot evaluation behavior changed, refresh before relying on detailed troubleshooting.
