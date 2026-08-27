# Repository Provenance

## Purpose

Read this file before deciding whether the operating graph matches a checkout.
If the commit, dirty paths, package facts, or major evidence paths differ,
refresh the repo skill before relying on detailed claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T10:09:55Z",
  "repository": {
    "name": "DRL-robot-navigation",
    "remote_url": "https://github.com/reiniscimurs/DRL-robot-navigation.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "1adfe511d6f3ff5d7d3bdc357914501c29646c39",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["TD3 modules are source files, not an installed distribution"]
    },
    {
      "name": "velodyne_description",
      "version": "1.0.10",
      "import_names": ["ROS package: velodyne_description"]
    },
    {
      "name": "velodyne_gazebo_plugins",
      "version": "1.0.10",
      "import_names": ["Gazebo/ROS plugin package"]
    }
  ],
  "evidence": {
    "source_roots": ["TD3", "catkin_ws/src/multi_robot_scenario", "catkin_ws/src/velodyne_simulator"],
    "docs": ["README.md", "catkin_ws/src/velodyne_simulator/README.md", "dockerfile"],
    "examples": ["TD3/train_velodyne_td3.py", "TD3/test_velodyne_td3.py", "catkin_ws/src/velodyne_simulator/velodyne_description/launch/example.launch"],
    "tests": [],
    "configs": ["TD3/assets/multi_robot_scenario.launch", "catkin_ws/src/multi_robot_scenario/launch", "catkin_ws/src/multi_robot_scenario/xacro", "catkin_ws/src/velodyne_simulator/velodyne_description/urdf"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the recorded commit.
- Recheck the dirty paths: the generated `skills/` tree is intentionally not
  part of the source baseline.
- Recheck the README's ROS/PyTorch baseline and the public TD3 filenames.
- Recheck the launch topic names and Velodyne macro parameters if the catkin
  workspace or vendored sensor package changes.
- This repository has no `pyproject.toml`, `setup.py`, or `setup.cfg`; a new
  Python distribution or console entry point is a material change.

The source checkout path and private inspection environment are deliberately
not recorded here.
