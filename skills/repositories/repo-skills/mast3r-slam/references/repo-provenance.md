# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
MASt3R-SLAM. If the commit, dirty state, package metadata, source roots,
third-party install layout, CUDA extension behavior, or public command-line
surface differs from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T18:40:21Z",
  "repository": {
    "name": "MASt3R-SLAM",
    "remote_url": "https://github.com/rmurai0610/MASt3R-SLAM.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "e6f4e3d474fad0e11f561482012be864ba8c3f17",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "Original source evidence was clean before generated skill and review artifacts were written under skills/."
  },
  "packages": [
    {
      "name": "MAST3R-SLAM",
      "version": "0.0.1",
      "import_names": ["mast3r_slam", "mast3r_slam_backends"]
    },
    {
      "name": "MAST3R",
      "version": "0.0.1",
      "import_names": ["mast3r", "dust3r"]
    },
    {
      "name": "in3d",
      "version": "0.0.1",
      "import_names": ["in3d"]
    },
    {
      "name": "lietorch",
      "version": "0.3",
      "import_names": ["lietorch"]
    }
  ],
  "evidence": {
    "source_roots": ["mast3r_slam", "main.py"],
    "package_metadata": ["pyproject.toml", "setup.py", "thirdparty/mast3r/pyproject.toml", "thirdparty/mast3r/setup.py", "thirdparty/in3d/pyproject.toml", "thirdparty/in3d/setup.py"],
    "docs": ["README.md", "Dependencies.md"],
    "configs": ["config/base.yaml", "config/calib.yaml", "config/eval_calib.yaml", "config/eval_no_calib.yaml", "config/eth3d.yaml", "config/intrinsics.yaml"],
    "scripts": ["scripts/download_tum.sh", "scripts/download_7_scenes.sh", "scripts/download_euroc.sh", "scripts/download_eth3d.sh", "scripts/eval_tum.sh", "scripts/eval_7_scenes.sh", "scripts/eval_euroc.sh", "scripts/eval_eth3d.sh"],
    "groundtruths": ["groundtruths/7-scenes", "groundtruths/euroc"],
    "resources": ["resources/programs"],
    "existing_repo_skills": ["skills/MASt3R-SLAM.log"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, refresh this skill.
- If package metadata no longer declares `MAST3R-SLAM` version `0.0.1`, or the
  root `setup.py` no longer compiles `mast3r_slam_backends`, refresh this skill.
- If `main.py --help` no longer exposes `--dataset`, `--config`, `--save-as`,
  `--no-viz`, and `--calib`, refresh runtime and evaluation guidance.
- If official config names, dataset scripts, or evaluation sequence lists change,
  refresh `run-slam` and `evaluation`.
- Treat generated files under `skills/` as construction artifacts; changes in
  the actual source/package/config/script paths above are the staleness signal.
