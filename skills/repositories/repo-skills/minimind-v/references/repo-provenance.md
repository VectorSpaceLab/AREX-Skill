# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of MiniMind-V. If the current repo commit, dirty state, package resources, public scripts, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T17:10:05Z",
  "repository": {
    "name": "minimind-v",
    "remote_url": "https://github.com/jingyaogong/minimind-v.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "740d467ece78a0b7d2d976fcb424472095d4a688",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["model", "dataset", "trainer"],
      "note": "script-style repository with no pyproject.toml, setup.py, or installable distribution metadata"
    }
  ],
  "evidence": {
    "source_roots": ["model", "dataset", "trainer"],
    "docs": ["README.md", "README_en.md", "model/model_init.md"],
    "examples": ["eval_vlm.py", "dataset/eval_images"],
    "scripts": ["scripts/convert_vlm.py", "scripts/web_demo_vlm.py", "trainer/train_pretrain_vlm.py", "trainer/train_sft_vlm.py"],
    "tests": [],
    "configs": ["requirements.txt", "model/tokenizer.json", "model/tokenizer_config.json"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty in source, model, dataset, trainer, scripts, or README files beyond generated `skills/` outputs, run `refresh-repo-skill`.
- If tokenizer files, public script arguments, model class signatures, checkpoint naming, SigLIP2 placement, parquet schema, or requirements change, run `refresh-repo-skill` even on the same commit.
- If a future release adds packaging metadata, new CLIs, tests, notebooks, multi-image/video branches, or changed model exports, refresh the skill before relying on this routing graph.
