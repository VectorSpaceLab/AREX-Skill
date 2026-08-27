# AlpaSim gRPC API reference

## Package and generated artifacts

The installable package is `alpasim_grpc`, with version metadata exposed as
`alpasim_grpc.__version__` and `alpasim_grpc.API_VERSION_MESSAGE`. Generated
modules live under `alpasim_grpc.v0` and are shipped by the package build.
The supported Python range is 3.11 through 3.12. The package uses `grpcio`,
`grpcio-tools`, and protobuf 4.x (`protobuf>=4,<5`); the build tooling pins
`setuptools<82` because the generator still imports `pkg_resources`.

For each schema file, the normal generated set is:

- `<name>_pb2.py`: message, enum, and descriptor classes;
- `<name>_pb2_grpc.py`: client stubs, servicer base classes, and server
  registration helpers;
- `<name>_pb2.pyi`: generated typing declarations when the build supports it.

Generated imports intentionally use the stable package path
`alpasim_grpc.v0`, including for services whose protobuf namespace is external.
Do not import generated modules by filesystem-relative names.

## Schema groups and service names

| Schema group | Generated modules | Service / important messages |
|---|---|---|
| `common` | `common_pb2` | Shared `Pose`, `Quat`, `Vec3`, `Trajectory`, `StateAtTime`, `VersionId`, and empty/status messages; no service |
| `controller` | `controller_pb2`, `controller_pb2_grpc` | `controller.VDCService`; session methods and `run_controller_and_vehicle` |
| `egodriver` | `egodriver_pb2`, `egodriver_pb2_grpc` | `egodriver.EgodriverService`; observations, route/ground truth, and `drive` |
| `logging` | `logging_pb2`, `logging_pb2_grpc` | `logging.LogEntry` and rollout metadata; it imports the other API groups |
| `physics` | `physics_pb2`, `physics_pb2_grpc` | `physics.PhysicsService`; ground intersection and scene/version queries |
| `runtime` | `runtime_pb2`, `runtime_pb2_grpc` | `RuntimeService`; `simulate`, scene prefetch, runtime info, shutdown |
| `sensorsim` | `sensorsim_pb2`, `sensorsim_pb2_grpc` | `nre.grpc.protos.sensorsim.SensorsimService`; RGB/LiDAR/aggregated rendering and availability queries |
| `traffic` | `traffic_pb2`, `traffic_pb2_grpc` | `traffic.TrafficService`; session, prediction, metadata, and scenes |
| `video_model` | `video_model_pb2`, `video_model_pb2_grpc` | `omnidreams.video_model.WorldModelService`; session and video chunk calls |

Use names from the generated module, not only the proto package. For example:

```python
from alpasim_grpc.v0 import common_pb2, runtime_pb2
from alpasim_grpc.v0.runtime_pb2_grpc import RuntimeServiceStub

request = runtime_pb2.SimulationRequest(
    rollout_specs=[runtime_pb2.RolloutSpec(scenario_id="example", nr_rollouts=1)]
)
# with grpc.insecure_channel("runtime-host:port") as channel:
#     result = RuntimeServiceStub(channel).simulate(request, timeout=30)
```

The example constructs and serializes a request but does not claim that
`example` exists or that the endpoint is reachable.

## Client and server shape

Generated clients are unary RPC callables. Create a channel, instantiate the
`*ServiceStub`, pass the corresponding `*_pb2` message, and set a bounded
`timeout` for a live call. Use `grpc.aio` only when the surrounding service is
async. A server implementation subclasses the generated `*Servicer` base and
registers it with the generated `add_*Servicer_to_server` function; that is a
service implementation concern owned by `runtime-services` or the relevant
component owner.

Use `common.Empty()` for empty requests. Treat `VersionId` and
`API_VERSION_MESSAGE` as version/provenance data, not as a health check. A
successful RPC depends on an endpoint, session state, scene/model data, and
compatible versions.

## Lifecycle after a schema edit

1. Update the `.proto` source while keeping field numbers stable. Reserve
   removed numbers/names rather than reusing them. Preserve imports and the
   external namespaces used by the sensor and video-model contracts.
2. Regenerate from the package project or call the bundled helper with an
   explicit proto root and output root.
3. Check that generated imports still resolve and that service method paths and
   request/response descriptors match the intended contract.
4. Review generated diffs and update callers/tests. Run focused tests and
   pre-commit. Do not commit a schema edit with stale generated artifacts.

The build hook regenerates artifacts for package builds. This does not remove
the need to regenerate and review them in a source checkout after editing a
schema.
