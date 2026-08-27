# Assets and Sensors Troubleshooting

## Missing catalog package

- **Likely cause:** the asset package was not installed into the active environment.
- **Recovery:** reinstall the standard Isaac Lab package set and verify the catalog helper output.

## Robot config spawns in the wrong place

- **Likely cause:** the initial pose was interpreted in the environment frame, not the world frame.
- **Recovery:** check the `init_state` position and joint fields before assuming the robot asset is broken.

## Joint names do not match

- **Likely cause:** joint keys were copied from an actuator group name instead of the USD joint names.
- **Recovery:** match the joint names used by the source asset and confirm the actuator groups separately.

## Contacts or camera data are missing

- **Likely cause:** the sensor is missing the runtime settings it needs.
- **Recovery:** enable contact reporting for contact sensors, and use a camera-capable visualizer or enable camera rendering for image sensors.

## Newton and PhysX behave differently

- **Likely cause:** the asset relies on solver-side drive assumptions that do not match the selected backend.
- **Recovery:** ensure the runtime settings request explicit drives when required and verify the backend-specific asset notes.

## A config does not appear in the catalog

- **Likely cause:** the config was not exported from the package namespace.
- **Recovery:** confirm that the config is part of the public catalog and that the helper script lists it in the expected namespace.
