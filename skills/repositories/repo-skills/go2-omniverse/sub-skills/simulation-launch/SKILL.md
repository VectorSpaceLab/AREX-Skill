---
name: simulation-launch
description: "Routes Go2 and G1 Isaac simulation startup, terrain and rendering
  options, checkpoint playback, and version-specific launcher troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Simulation launch

Use this route for Go2/G1 startup, `--headless`, rendering/capture, terrain,
robot count, checkpoint discovery, G1 asset setup, or Isaac version selection.

## Select the launcher

1. Use the bundled `scripts/launch_sim.sh` adapter for the modern Isaac Sim 5
   + bundled Jazzy route; pass `--robot go2` or `--robot g1`.
2. Use `--twinbot` on that adapter only after reading the
   [`digital-twin`](../digital-twin/SKILL.md) route and confirming the external
   bridge topics.
3. Use `--ros-distro humble` only when an Isaac Sim 6 / IsaacLab 4.5.22 /
   bundled Humble installation is already available; this compatibility route
   is documented but not verified by this skill.

Do not source host `/opt/ros/jazzy` into the modern Isaac Python process. Let the
launcher select the bundled ROS extension and set its library paths.

## Minimal workflow

- Run [`scripts/check_runtime_prereqs.py`](../../scripts/check_runtime_prereqs.py)
  first; it is read-only.
- Use [`scripts/launch_sim.sh`](scripts/launch_sim.sh) as the bundled launcher
  adapter. It requires an explicit `--project-root` containing the runtime
  application and never sources host ROS.
- Confirm a compatible NVIDIA driver/GPU, the exact Isaac Sim/IsaacLab versions,
  the policy checkpoint, and the G1 USD when using G1.
- Start with one robot, flat terrain, and `--headless`; add rough terrain,
  cameras, capture, or multiple robots one change at a time.
- Treat `all imports complete`, `gym.make: done`, `ROS2 publishers up`, and
  `entering main loop` as useful progress signals, not as proof of stable
  long-running behavior.

See [`references/launchers.md`](references/launchers.md) for flag combinations,
[`references/simulation-api.md`](references/simulation-api.md) for source-backed
configuration facts, and [`references/troubleshooting.md`](references/troubleshooting.md)
for failure recovery. Version comparisons are in
[`references/compatibility.md`](references/compatibility.md).

## Verification limitation

The repository requires IsaacLab 0.54.3, which was unavailable during skill
construction. CUDA and Isaac Sim package smoke checks passed, but this route
must not claim a successful repository boot or live IsaacLab API verification.
The first full-runtime check after obtaining the matching package should be a
bounded Go2 flat/headless launch before G1, capture, or twinbot.
