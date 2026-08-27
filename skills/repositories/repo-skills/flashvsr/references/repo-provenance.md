# Repository Provenance

Read this before deciding whether the FlashVSR operating skill is current for a
checkout. If the commit, dirty state, package version, or major evidence paths
differ, run a refresh rather than assuming the runtime graph is still aligned.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T17:41:18Z",
  "repository": {
    "name": "FlashVSR",
    "remote_url": "https://github.com/OpenImagingLab/FlashVSR.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "6dd38e57203af4efca97df82c659f5d5a2dcf51a",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "diffsynth",
      "version": "1.1.7",
      "import_names": ["diffsynth"]
    }
  ],
  "evidence": {
    "source_roots": ["diffsynth/pipelines", "diffsynth/models", "diffsynth/vram_management"],
    "docs": ["README.md", "requirements.txt", "setup.py"],
    "examples": ["examples/WanVSR/infer_flashvsr_full.py", "examples/WanVSR/infer_flashvsr_tiny.py", "examples/WanVSR/infer_flashvsr_tiny_long_video.py", "examples/WanVSR/infer_flashvsr_v1.1_full.py", "examples/WanVSR/infer_flashvsr_v1.1_tiny.py", "examples/WanVSR/infer_flashvsr_v1.1_tiny_long_video.py"],
    "tests": [],
    "configs": ["diffsynth/configs/model_config.py"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the snapshot commit.
- Recheck the dirty path summary; the generated `skills/` tree is construction
  output and is not source evidence.
- Refresh if FlashVSR pipeline exports, the Wan DiT attention backend, model
  file names, frame geometry rules, or the pinned runtime requirements change.
