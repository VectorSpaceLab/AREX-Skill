# Repository Provenance

## Purpose

Read this before deciding whether this skill still matches a checkout of HunyuanVideo-I2V. If the commit, dirty state, or public evidence paths differ, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-19T13:26:33Z",
  "repository": {
    "name": "HunyuanVideo-I2V",
    "remote_url": "https://github.com/Tencent-Hunyuan/HunyuanVideo-I2V.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "c8bba70b9517f08d770a9a2a3d1e93cc6d5b7949",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "HunyuanVideo-I2V",
      "version": null,
      "import_names": ["hyvideo"]
    }
  ],
  "evidence": {
    "source_roots": ["hyvideo", "sample_image2video.py", "train_image2video_lora.py"],
    "docs": ["README.md", "README_zh.md", "ckpts/README.md", "hyvideo/hyvae_extract/README.md"],
    "examples": ["assets/demo/i2v", "assets/demo/i2v_lora"],
    "tests": [],
    "configs": ["requirements.txt", "hyvideo/hyvae_extract/vae.yaml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` changes, treat the skill as stale and refresh it.
- If the working tree becomes dirty or the dirty paths differ from this snapshot, refresh it.
- If public CLI flags, dependencies, or checkpoint layout change on the same commit, refresh it.
