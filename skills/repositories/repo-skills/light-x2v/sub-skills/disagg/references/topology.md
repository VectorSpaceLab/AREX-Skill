# Disaggregation Topology

## Role map

| Role | Responsibility | Common entry point |
| --- | --- | --- |
| controller | Accepts requests, schedules roles, manages instances | `python -m lightx2v.disagg.examples.run_service --service controller ...` |
| encoder | Builds request buffers and input-side payloads | `python -m lightx2v.disagg.examples.run_service --service encoder ...` |
| transformer | Runs the core model work | `python -m lightx2v.disagg.examples.run_service --service transformer ...` |
| decoder | Produces the final image/video/audio output | `python -m lightx2v.disagg.examples.run_service --service decoder ...` |
| user | Generates and sends request workloads | `python -m lightx2v.disagg.examples.run_user ...` |

## Important config fields

The disaggregation config usually determines:
- `disagg_mode`
- role ranks such as `encoder_engine_rank`, `transformer_engine_rank`, and `decoder_engine_rank`
- request / result ports
- RDMA or Mooncake bootstrap addresses
- monitor bindings and log output locations
- the model family and task that the role should run

## Common environment variables

These are the most common knobs that appear in the shell launchers and service code:

- `DISAGG_TOPOLOGY`
- `DISAGG_CONTROLLER_CFG`
- `DISAGG_CONDA_ENV`
- `DISAGG_SKIP_CONDA_ACTIVATE`
- `DISAGG_CONTROLLER_HOST`
- `DISAGG_CONTROLLER_REQUEST_PORT`
- `DISAGG_INSTANCE_START_TIMEOUT_SECONDS`
- `DISAGG_REMOTE_PROXY_START_TIMEOUT_SECONDS`
- `DISAGG_SIDECAR_START_TIMEOUT_SECONDS`
- `CONTROLLER_WAIT_TIMEOUT_S`
- `CONTROLLER_POLL_INTERVAL_S`
- `RDMA_IFACE`
- `MOONCAKE_DEVICE_NAME`
- `MOONCAKE_LOCAL_HOSTNAME`
- `RDMA_PREFERRED_IPV4`
- `SYNC_COMM`
- `LOAD_FROM_USER`
- `DISAGG_AUTO_REQUEST_COUNT`
- `USER_MAX_REQUESTS`

## Planner helper use

The bundled planner helper prints a safe command plan from a config file before you run a live deployment. Use it when you need to understand the topology without starting processes.
