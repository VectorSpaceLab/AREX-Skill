# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the LLaVA repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T14:45:00Z",
  "repository": {
    "name": "LLaVA",
    "remote_url": "https://github.com/haotian-liu/LLaVA.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "c121f0432da27facab705978f83c4ada465e46fd",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "llava",
      "version": "1.2.2.post1",
      "import_names": ["llava"]
    }
  ],
  "evidence": {
    "source_roots": ["llava/"],
    "docs": [
      "README.md",
      "docs/Data.md",
      "docs/Evaluation.md",
      "docs/Finetune_Custom_Data.md",
      "docs/LoRA.md",
      "docs/MODEL_ZOO.md",
      "docs/ScienceQA.md",
      "docs/macOS.md",
      "docs/Windows.md",
      "docs/Intel.md",
      "docs/Customize_Component.md",
      "docs/LLaVA_from_LLaMA2.md"
    ],
    "scripts": [
      "scripts/",
      "scripts/v1_5/",
      "predict.py",
      "cog.yaml"
    ],
    "tests": [],
    "configs": [
      "pyproject.toml",
      "scripts/zero2.json",
      "scripts/zero3.json",
      "scripts/zero3_offload.json"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source, docs, package metadata, or script changes not represented above, run `refresh-repo-skill`.
- The dirty path above records generated skill/log artifacts under `skills/`; ignore generated review artifacts when deciding whether the source package changed, but do refresh if package code, docs, scripts, configs, or metadata changed.
- If package metadata, public module entry points, CLI flags, or major checkpoint families changed even on the same commit, run `refresh-repo-skill`.

## Evidence Notes

This skill was built from public LLaVA package evidence and live import/signature checks of `llava` version `1.2.2.post1`. No generated runtime instruction requires a source checkout path. Large model downloads, full benchmark runs, full training, optional SGLang, optional FlashAttention/xFormers, MPS/Intel variants, and OpenAI-based judging were treated as documented or optional workflows rather than fully executed native checks.
