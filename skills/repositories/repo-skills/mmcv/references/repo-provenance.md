# Repository Provenance

## Purpose

Read this before deciding whether this MMCV skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-30T00:00:00Z",
  "repository": {
    "name": "mmcv",
    "remote_url": "https://github.com/open-mmlab/mmcv.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "a8073c74bf83d62ec36a103f835faa4837fb6585",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "mmcv-lite",
      "version": "2.2.0",
      "import_names": ["mmcv"],
      "notes": "Source builds with MMCV_WITH_OPS=0 install as mmcv-lite and do not include compiled mmcv._ext ops."
    },
    {
      "name": "mmcv",
      "version": "2.2.0",
      "import_names": ["mmcv"],
      "notes": "Full package variant includes compiled ops when installed or built with compatible backend support."
    }
  ],
  "evidence": {
    "source_roots": ["mmcv/"],
    "docs": ["README.md", "docs/en/"],
    "package_metadata": ["setup.py", "setup.cfg", "MANIFEST.in", "requirements/", "requirements.txt"],
    "scripts": [".dev_scripts/check_installation.py"],
    "tests": ["tests/test_arraymisc.py", "tests/test_image/", "tests/test_video/", "tests/test_visualization.py", "tests/test_transforms/", "tests/test_cnn/", "tests/test_ops/", "tests/test_utils/test_env.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If public modules under `mmcv/`, docs under `docs/en/`, package metadata, or relevant tests change, run `refresh-repo-skill`.
- If package variant semantics change, especially `mmcv` versus `mmcv-lite` or `MMCV_WITH_OPS`, run `refresh-repo-skill`.
- Ignore the generated `skills/` directory itself when comparing source evidence unless the task is to refresh this skill.
