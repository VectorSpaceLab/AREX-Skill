# Developer workflows

## Package and entry-point inspection

Start with package metadata rather than importing every optional model:

```bash
python -c 'import alpasim_grpc; print(alpasim_grpc.__version__)'
python -c 'from alpasim_grpc.v0 import common_pb2, runtime_pb2_grpc; print(common_pb2.VersionId.DESCRIPTOR.full_name)'
alpasim-info
```

For a structured view that does not instantiate plugins, inspect entry points:

```python
from importlib.metadata import entry_points
for group in ("alpasim.models", "alpasim.mpc", "alpasim.scorers", "alpasim.tools", "alpasim.configs"):
    print(group, sorted(ep.name for ep in entry_points(group=group)))
```

`alpasim_plugins.PluginRegistry` loads each entry point lazily on the first
registry query, logs failures, caches successful loads, and raises on duplicate
names. `get_plugin_info()` covers the five groups above. A package that adds a
model normally declares `alpasim.models`; a package that contributes Hydra
configuration declares `alpasim.configs` as well. The entry-point value must be
an importable `module:object`, and the declared dependency must point toward
generic APIs, not from a generic package into a deployment-specific plugin.

## Safe proto-change checklist

```text
[ ] Identify the owning service and all imported schemas.
[ ] Keep field numbers, package names, and wire types compatible.
[ ] Regenerate with compile-protos or the bundled explicit-path helper.
[ ] Inspect the generated diff; confirm no unrelated generated files changed.
[ ] Import every touched *_pb2 and *_pb2_grpc module.
[ ] Run a focused test, then pre-commit for the contributor change.
[ ] Record endpoint/version/backend assumptions in the change review.
```

A minimal serialization check can be run without a server:

```python
from alpasim_grpc.v0 import common_pb2, sensorsim_pb2
message = common_pb2.Pose(vec=common_pb2.Vec3(x=1.0))
round_trip = common_pb2.Pose.FromString(message.SerializeToString())
assert round_trip == message
request = sensorsim_pb2.RGBRenderRequest(scene_id="fixture")
assert request.scene_id == "fixture"
```

This checks the generated descriptors and protobuf wire round-trip only; it
cannot validate renderer behavior, camera calibration, scene availability, or
service timing.

## Focused contributor checks

- Protobuf: compile, generated imports, serialization smoke, and the relevant
  gRPC boundary test.
- Plugins: `alpasim-info`, entry-point listing, and the plugin registry tests.
- Slurm helper logic: run only its fixture-based unit test; do not call
  `sbatch`, `scontrol requeue`, or an actual cluster.
- Map helper: use a small disposable fixture and a non-interactive plotting
  backend if optional map dependencies are installed. Route map semantics and
  trajectory interpretation to `evaluation-and-logs`.
- General changes: run the narrowest pytest target and `pre-commit run
  --all-files`; distinguish missing optional extras from assertion failures.

## Extension review

For a new service, decide whether it belongs in an existing schema group or
needs a new versioned group. Define request/response messages, service methods,
version reporting, session ownership, and coordinate-frame semantics together.
Update all generated artifacts and any logging/replay messages that embed the
contract. Keep runtime/service orchestration out of the generic gRPC package.

For a plugin, declare its entry-point group and import target in package
metadata, keep the plugin package dependent on the generic registry/API, and
add a focused registry/config test. If the plugin needs model weights, CUDA,
compiled extensions, gated data, or external services, document those as
optional prerequisites rather than making import failure silently look like an
empty registry.

## Coordinate-frame review

Use explicit names such as `position_object_in_local` and
`pose_local_to_ego_rig`. The main frames are:

- `local`: scenario-fixed inertial ENU frame;
- `rig`: body-fixed frame, x forward, y left, z up, origin at the rear axle
  projected to ground;
- `aabb`: body-fixed orientation with origin at the object bounding-box center;
- `ecef`: WGS84 Earth-centered global frame;
- estimated/noised variants: policy-facing estimates, not ground truth.

AlpaSim uses active `A->B` transforms to move an object. A passive coordinate
change uses the inverse. Name vectors and transforms with both endpoints and
the frame. In service reviews, check that driver routes/ground truth,
controller state and trajectory, physics/traffic AABB poses, renderer
calibration, and log actor poses are not mixed casually. See the API reference
for the service-specific summary.
