# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of `gym-pybullet-drones`. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T13:04:27Z",
  "repository": {
    "name": "gym-pybullet-drones",
    "remote_url": "https://github.com/learnsyslab/gym-pybullet-drones.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "90c97ef3d97ce5de90ca720537707ff1ee97efb8",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "gym-pybullet-drones",
      "version": "2.2.0",
      "import_names": ["gym_pybullet_drones"]
    }
  ],
  "evidence": {
    "source_roots": ["gym_pybullet_drones"],
    "docs": ["README.md"],
    "examples": ["gym_pybullet_drones/examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", ".github/workflows/test.yml"],
    "assets": ["gym_pybullet_drones/assets/*.urdf", "gym_pybullet_drones/assets/beta-traj.csv", "gym_pybullet_drones/assets/eeprom.bin", "gym_pybullet_drones/assets/clone_bfs.sh", "gym_pybullet_drones/assets/ffmpeg_png2mp4.sh"]
  }
}
```

The dirty path at capture is the generated skill/review artifact area under `skills/`; package source, README, tests, and metadata were the source evidence for this skill.

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source-code changes outside generated `skills/` artifacts, run `refresh-repo-skill` before relying on source-level API or workflow details.
- If package metadata, dependencies, registered Gymnasium IDs, example signatures, or public environment/controller APIs changed even on the same commit, run `refresh-repo-skill`.
