# Custom robots and assets

## Minimal custom robot path

1. Create an MJCF file with a floating base, joint limits, axes, and collision geometries.
2. Add a robot config class with body mappings, trackable bodies, asset config, default root height, PD controls, and per-simulator params.
3. Register the robot name in the factory.
4. Run factory/config smokes.
5. Validate with a random-pose or simple simulator check.
6. Only then train or retarget motions.

## Robot config fields to review

- `common_naming_to_robot_body_names`: maps semantic names such as feet, hands, head, and torso to robot-specific body names.
- `trackable_bodies_subset`: bodies used for MaskedMimic or sparse control surfaces.
- `asset`: MJCF path, self-collisions, fixed base, gravity, and asset-root behavior.
- `default_root_height`: standing/reset height.
- `control`: PD stiffness/damping/effort/velocity limits, often selected by regex patterns.
- `simulation_params`: per-backend FPS, decimation, solver, and friction parameters.

## MJCF and USD

MJCF is the source of truth for humanoid assets in the distilled snapshot. IsaacLab consumes USD, so ProtoMotions lazily converts MJCF to USD at scene construction and caches by MJCF fingerprint plus conversion options.

Important IsaacLab helper behavior:

- Config kwargs are built without importing Kit.
- Real conversion imports IsaacLab/Kit only inside the converter factory.
- Cache invalidation includes MJCF and referenced mesh/texture fingerprints.
- A D6 workaround repairs overconstrained MuJoCo joint conversion details until upstream behavior is fixed.
- Body prim paths and articulation roots can be resolved from lightweight records in tests without Kit.

## Testing order

1. `robot_config("new_name")` factory import.
2. `simulator_config(...)` for each selected backend.
3. Asset path resolution and MJCF existence.
4. Kit-free helper/unit tests where possible.
5. One-env random-pose or load-robot visualizer with the selected backend.
6. Motion retargeting and training only after robot load is stable.

## Cross-simulator considerations

Changing simulator can change quaternion convention, friction combine mode, PD behavior, contact dynamics, and joint representation. Use ProtoMotions helper functions where available and validate transfer empirically.
