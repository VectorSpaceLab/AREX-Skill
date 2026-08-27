# Launcher reference

Use the bundled `scripts/launch_sim.sh` adapter for environment wiring. It
accepts an explicit project root so the generated skill does not depend on the
adapter's own directory. Run it only in an operator's compatible checkout with
the required external stack.

## Modern Isaac Sim 5 / bundled Jazzy

```bash
bash sub-skills/simulation-launch/scripts/launch_sim.sh \
  --project-root "$PWD" --isaac-venv "$ISAAC_VENV" \
  --robot go2 --robot-amount 1 --terrain flat --headless
bash sub-skills/simulation-launch/scripts/launch_sim.sh \
  --project-root "$PWD" --isaac-venv "$ISAAC_VENV" \
  --robot g1 --robot-amount 1 --headless
```

The launchers set these defaults unless the operator overrides them:

| Variable | Modern default | Meaning |
|---|---|---|
| `ISAAC_VENV` | operator-selected path | Isaac Python 3.11 environment |
| `ISAACLAB_PATH` | operator-selected path | Optional source checkout/asset context |
| `OMNI_KIT_ACCEPT_EULA` | `YES` | Non-interactive Isaac Sim startup |
| `ROS_DISTRO` | `jazzy` | Bundled ROS runtime selected by the launcher |
| `RMW_IMPLEMENTATION` | `rmw_fastrtps_cpp` | DDS implementation for the sim side |

The launcher discovers the bundled ROS extension under
`isaacsim.ros2.core` or the older `isaacsim.ros2.bridge` layout, then prepends
its `rclpy` and native library directories. Do not manually append host ROS
paths afterward.

## Common app flags

`--headless` avoids a GUI window. `--robot go2|g1` selects the robot. Use
`--robot_amount N` for multiple scene instances. `--terrain flat|rough` selects
the plane or generated stair terrain. `--task` selects the registered IsaacLab
task; keep the repository default unless the target installation exposes a
compatible task registry.

For a camera capture, add `--enable_cameras`, `--capture N`,
`--capture_dir <operator-owned-output>`, and a rendering preset such as
`--rendering_mode quality`. Start with a small settle count and a writable
output directory; capture may require remote Isaac assets and shader caches.

## Isaac Sim 6 / bundled Humble

The bundled adapter also accepts `--ros-distro humble` and expects the Isaac
Sim 6 `isaacsim.ros2.core/{humble}/` layout. It is a separate compatibility
route, not a drop-in replacement for the modern Jazzy environment. Do not mix
its Python or bundled libraries into an Isaac Sim 5 environment.
