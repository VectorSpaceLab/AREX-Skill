# Simulation launch troubleshooting

## Missing required package

`ModuleNotFoundError: isaaclab` or failures before `AppLauncher: ready` mean the
exact IsaacLab/Isaac Sim installation is not present or is incompatible. Install
or expose the repository-documented matching stack in a private environment;
do not replace it silently with a current IsaacLab release.

## ROS library conflict

If `rclpy` or native typesupport fails to load, remove host ROS paths from the
modern Isaac process and use the launcher-managed bundled Jazzy paths. Do not
source `/opt/ros/jazzy` after the launcher has configured `PYTHONPATH` and
`LD_LIBRARY_PATH`.

## Checkpoint selection

The runtime searches the configured experiment directory using `load_run` and
`load_checkpoint` patterns. Confirm the experiment name (`unitree_go2_rough`
or `g1_rough`) and checkpoint architecture before changing the pattern. A
missing checkpoint is a data/artifact problem, not a CUDA fix.

## G1 or custom environment asset

A missing G1 USD or downloaded office/warehouse asset must be resolved by the
operator. Start with Go2 flat terrain to isolate runtime issues. Do not point a
public skill instruction at a machine-specific absolute asset path.

## Headless and capture

Use `--headless` for a no-window smoke. Add camera enablement and capture only
after the basic loop reaches `entering main loop`. First-run shader compilation,
remote asset availability, camera API changes, and unwritable capture directories
can all fail independently.
