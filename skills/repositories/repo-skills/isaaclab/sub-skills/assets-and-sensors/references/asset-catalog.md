# Asset Catalog

## What this package provides

`isaaclab_assets` is the repository’s ready-made catalog of robot and sensor configuration objects. It is importable on its own and exports the catalog through two main namespaces:

- `isaaclab_assets.robots`
- `isaaclab_assets.sensors`

The top-level package also re-exports the most common catalog entries for convenience.

## What to expect in the catalog

Representative robot families include:

- Franka
- Unitree
- ANYmal
- Spot
- Allegro
- Humanoids
- Quadcopters
- Cartpole and other classic-control robots

Representative sensors include:

- GelSight tactile sensors
- Velodyne lidar configs

## Practical usage

- Import a catalog config and assign it directly to the relevant scene or environment field.
- Use the catalog as the starting point for a custom robot or sensor config instead of building one from scratch.
- When a config is missing, extend the package with a new config object that follows the same dataclass pattern.

## What the catalog is not

- It is not the simulation launcher.
- It is not the task registry.
- It is not the RL wrapper layer.

Those workflows live in the other sub-skills.
