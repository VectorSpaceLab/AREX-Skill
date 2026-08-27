# Service lifecycle and address routing

Read this when starting the runtime outside the usual launcher, using daemon
mode, replacing one service for debugging, or investigating ports and shutdown.

## One-shot path

The runtime receives a user config, a generated network config, an evaluation
config, and a log directory. Startup proceeds in this order:

1. Parse typed user/network/evaluation configuration.
2. Build the scene loader and check configured scene IDs.
3. Probe non-skipped service addresses for API/version identity and require a
   consistent version per service across all addresses.
4. Build address pools and worker runtime.
5. Optionally warm scene-affine renderer cache state.
6. For each rollout, assign one address from each required pool, open service
   sessions, run the event loop, collect the result, release slots, and mark
   successful output complete.
7. Stop workers and managed services according to the shutdown setting.

A skipped service receives a synthetic skipped version and is not probed. A
non-skipped service with no address is a configuration error. Mixed versions
across replicas fail startup because the runtime records one canonical version
identity per service.

The direct module CLI requires these flags:

```text
python -m alpasim_runtime.simulate \
  --user-config <resolved-user.yaml> \
  --network-config <generated-network.yaml> \
  --log-dir <run-dir> \
  --eval-config <eval.yaml>
```

Use `--log-level DEBUG` only for a bounded diagnostic run; it can produce large
logs. `--array-job-dir` is required when running as a Slurm array and is used
for aggregation context. Deployment generation and container lifecycle belong
to `simulation-wizard`.

## Daemon path

Daemon mode adds a runtime gRPC server while the runtime remains a central
client of backing services. A typical sequence is:

1. Start the runtime with `--serve` and a listen address, or let the deployment
   route provide one.
2. Wait for the runtime port to accept connections; a generated address file is
   discovery metadata, not proof that startup is finished.
3. Call runtime discovery to inspect renderer type, known scenes, worker count,
   maximum concurrent rollouts, service capacities, and version IDs.
4. Submit a request with known scene IDs and valid rollout specifications.
5. Wait for the returned per-rollout status/metrics, then request shutdown.

`SimulationRequest` expansion creates one job per `nr_rollouts`. A spec with
zero rollouts is dropped. If `session_uuids` is supplied, its length must equal
`nr_rollouts`. Unknown scenes are rejected. Video-model requests reject a
nonzero `start_time_offset_us`. Per-request `available_drivers` require
`n_concurrent_per_driver >= 1`; those addresses override only the driver pool.

The daemon engine is idempotent for repeated startup/shutdown calls. Shutdown
stops accepting requests, cancels cache prefetch, fails queued jobs, stops the
dispatch loop, and stops workers. In-flight work is not guaranteed to drain
once the scheduler is shut down; clients should not submit new work during this
phase.

## Address pools and scene affinity

The network config maps each service name to endpoint records with an address
and managed flag. The runtime selects generated gRPC stubs from the renderer
kind: sensorsim uses its renderer stub; video-model uses the world-model stub.
Managed-only filtering controls which endpoints the runtime owns for shutdown;
external endpoints can still be used as clients when configured.

The scheduler greedily reserves a renderer slot, acquires the remaining service
slots, then submits an assigned job to a worker. FIFO dispatch is the default.
Scene-affine dispatch adds a cache-aware tier: confirmed cached scenes are
preferred, then bounded cold loads are placed on eligible renderer addresses.
Cache snapshots are authoritative for completed loads; a pending load remains
in-flight until confirmed or its rollout result updates local state.

## Safe replacement/debugging boundary

To replace one service, generate the deployment files without running the
simulation, start the other services, and make the replacement listen on the
exact allocated address. The replacement must implement the expected gRPC
service contract and version method. Keep the runtime's generated network config
unchanged; changing only the replacement's port is a common source of
`UNAVAILABLE` errors. Proto/stub details belong to `grpc-and-developer-tools`.

For a breakpoint run, prefer `nr_workers=1`, one scene, one rollout, and
`--log-level DEBUG`. Keep the runtime process separate from long-lived backing
services and use the runtime's own output as the one-shot completion signal.
Never treat a manually started service as managed merely because it is on the
same host.
