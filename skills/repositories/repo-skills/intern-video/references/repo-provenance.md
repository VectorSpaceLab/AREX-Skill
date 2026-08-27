# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package metadata, public entry points, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T09:45:00Z",
  "repository": {
    "name": "InternVideo",
    "remote_url": "https://github.com/OpenGVLab/InternVideo.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "3965eef16e2dadd0ea6c8d0cc29c8a3039df52e3",
    "working_tree": "clean-before-generated-skill-output",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "internvideo2_multi_modality",
      "version": "0.1.0",
      "import_names": ["internvideo2_multi_modality"]
    },
    {
      "name": "xtuner",
      "version": null,
      "import_names": ["xtuner"]
    }
  ],
  "evidence": {
    "source_roots": [
      "InternVideo1",
      "InternVideo2/single_modality",
      "InternVideo2/multi_modality",
      "InternVideo-Next",
      "InternVideo3/InternVideo3_sft"
    ],
    "docs": [
      "README.md",
      "CLAUDE.md",
      "InternVideo1/README.md",
      "InternVideo2/README.md",
      "InternVideo2/single_modality/README.md",
      "InternVideo2/single_modality/INSTALL.md",
      "InternVideo2/single_modality/DATASET.md",
      "InternVideo2/single_modality/MODEL_ZOO.md",
      "InternVideo2/multi_modality/README.md",
      "InternVideo2/multi_modality/INSTALL.md",
      "InternVideo2/multi_modality/DATASET.md",
      "InternVideo2/multi_modality/MODEL_ZOO.md",
      "InternVideo2/multi_modality/DEMO_USAGE_GUIDE.md",
      "InternVideo2.5/README.md",
      "InternVideo3/README.md",
      "InternVideo3/InternVideo3_sft/README.md",
      "InternVideo-Next/README.md",
      "InternVideo-Next/MODEL_ZOO.md",
      "Data/InternVid/README.md",
      "Data/instruction_data/README.md"
    ],
    "examples": [
      "Data/InternVid/demo.ipynb",
      "InternVideo2/multi_modality/demo_video_text_retrieval.ipynb"
    ],
    "tests": [
      "InternVideo2/multi_modality/tests"
    ],
    "configs": [
      "InternVideo2/multi_modality/configs",
      "InternVideo2/multi_modality/scripts/evaluation",
      "InternVideo3/InternVideo3_sft/configs"
    ],
    "scripts": [
      "InternVideo2/single_modality/scripts",
      "InternVideo2/multi_modality/scripts",
      "InternVideo2/multi_modality/tools",
      "InternVideo2/multi_modality/preprocess",
      "InternVideo3/InternVideo3_sft/scripts",
      "InternVideo3/InternVideo3_eval/scripts",
      "InternVideo3/scripts"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as potentially stale.
- If package metadata for `internvideo2_multi_modality` or `xtuner` changes, refresh API/config guidance.
- If new model generations, benchmark scripts, or dataset releases appear, update `series-map`, `video-mllm`, and `datasets` first.
- Generated skill output was excluded from the source baseline; do not count the `skills/` files created by this production as evidence that the original repo was dirty.
