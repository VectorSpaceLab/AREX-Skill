# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of HunyuanVideo. If the current repo commit, dirty state, package metadata, public entry points, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-12T16:29:14Z",
  "repository": {
    "name": "HunyuanVideo",
    "remote_url": "https://github.com/Tencent-Hunyuan/HunyuanVideo.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "e748c73ac064728bf6bd15b1cdb8161e55a4f331",
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
        "hyvideo"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "hyvideo"
    ],
    "docs": [
      "README.md",
      "README_zh.md",
      "ckpts/README.md"
    ],
    "examples": [
      "sample_video.py",
      "gradio_server.py",
      "scripts/run_sample_video.sh",
      "scripts/run_sample_video_fp8.sh",
      "scripts/run_sample_video_multigpu.sh"
    ],
    "tests": [
      "tests/test_attention.py"
    ],
    "configs": [
      "requirements.txt",
      "hyvideo/config.py",
      "hyvideo/constants.py"
    ],
    "scripts": [
      "utils/collect_env.py",
      "hyvideo/utils/preprocess_text_encoder_tokenizer_utils.py"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale.
- If public files such as `README.md`, `ckpts/README.md`, `hyvideo/config.py`, `hyvideo/inference.py`, `sample_video.py`, `gradio_server.py`, or the shell scripts change, refresh the skill.
- If HunyuanVideo gains package metadata, new entry points, training/evaluation workflows, or changed checkpoint layout, refresh the skill.
