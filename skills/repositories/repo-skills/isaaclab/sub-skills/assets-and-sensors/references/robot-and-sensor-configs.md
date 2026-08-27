# Robot and Sensor Configs

## Robot configs

Most ready-made robot configs are `ArticulationCfg` objects.

Typical fields:

- `spawn` — the USD or URDF source for the robot
- `actuators` — the control model for each joint group
- `init_state` — the default pose and joint state used at spawn or reset

Useful patterns:

- Use `UsdFileCfg` when the robot is authored as a USD asset.
- Use `UrdfFileCfg` when you need to import a URDF directly.
- Use `ImplicitActuatorCfg` when the physics solver should handle the joint drive directly.
- Use `ExplicitActuatorCfg` or related explicit actuator models when the actuation logic should be modeled in Python.

### Important robot details

- Initial positions are defined in the local environment frame, not the world frame.
- Joint names in `init_state.joint_pos` must match the USD joint names, not the actuator group names.
- The `ensure_drives_exist` style of configuration is important when a backend needs explicit USD drives to exist.
- `actuator_value_resolution_debug_print` can help when the runtime values differ from the USD defaults.

## Sensor configs

Common sensor config families include:

- `CameraCfg`
- `RayCasterCfg`
- `ContactSensorCfg`
- `FrameTransformerCfg`

Key ideas:

- `update_period` controls how often a sensor refreshes.
- Camera sensors need a compatible visualizer or camera-enabled run.
- Ray-caster sensors are often used for height scanning or contact-like probes.
- Contact sensors rely on contact reporting being enabled on the rigid bodies they observe.

## Data access

- Asset and sensor data is exposed through the object’s `data` attribute.
- Access patterns vary by asset type, but the general rule is to use the provided `data` view instead of reaching into implementation-specific buffers.
- When migrating old scripts, prefer the current proxy-aware data access patterns described in the root workflow map and helper scripts.
