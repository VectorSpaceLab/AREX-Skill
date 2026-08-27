# Repository Provenance

Read this before deciding whether the operating skill still matches a newer
checkout. Refresh it when the commit, dirty paths, launcher behavior, public
ROS topic contract, or Isaac version assumptions change.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T20:01:42Z",
  "repository": {
    "name": "go2_omniverse",
    "remote_url": "https://github.com/abizovnuralem/go2_omniverse",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "db18970d66fa77a68bf0976b0f7c183825cd2292",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [],
  "evidence": {
    "source_roots": ["root Python modules", "robots/g1", "go2_omniverse_ws/src/go2_interfaces"],
    "docs": ["README.md", "JAZZY.md", "docs/TWINBOT_IMU_FIX.md"],
    "examples": ["run_sim.sh", "run_sim_g1.sh", "run_sim_humble.sh", "run_twinbot.sh"],
    "tests": [],
    "configs": ["Isaac_sim/Unitree/Unitree_L1.json", "agent_cfg.py", "terrain_cfg.py", "terrain_generator_cfg.py", "robots/g1/config.py"]
  }
}
```

There is no repository Python distribution metadata or package version. The
checkout contains large policy checkpoints and a binary G1 asset; these remain
runtime prerequisites rather than generated skill dependencies.

## Refresh checks

- If the Git commit differs, run `refresh-repo-skill` before trusting API or
  launcher details.
- If launcher scripts change Isaac Sim/IsaacLab versions, ROS distro, RMW,
  extension paths, or environment variables, refresh the simulation and ROS
  routes.
- If `ros2.py`, `twinbot.py`, `scripts/twinbot_bridge.py`, or the custom message
  files change, refresh telemetry and digital-twin mappings.
- If a matching IsaacLab 0.54.3 environment becomes available, re-run the
  blocked native verification cases before treating the skill as complete.
