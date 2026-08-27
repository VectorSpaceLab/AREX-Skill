---
name: distributed-tuning
id: distributed-tuning
description: "Routes KerasTuner's chief/worker Oracle coordination over gRPC
  using the KERASTUNER_ORACLE_IP, KERASTUNER_ORACLE_PORT, and
  KERASTUNER_TUNER_ID environment contract."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Distributed Tuning

Use this sub-skill when a KerasTuner search must coordinate multiple tuner
processes through a chief Oracle, or when a `KERASTUNER_ORACLE_*`/
`KERASTUNER_TUNER_ID` deployment is failing.

## Scope

- Configure the three distributed Oracle environment variables as one unit.
- Assign chief and worker roles, launch the gRPC service, and diagnose network
  and shared-storage prerequisites.
- Understand OracleClient request, status, reporting, and shutdown behavior.
- Keep distributed Oracle coordination separate from the model/search-space
  design handled by the main KerasTuner workflow.

Do not use this route for a local single-process search, CloudOracle-managed
distribution, or general `HyperParameters`/tuner selection. In particular,
the `Tuner` public contract supports only **single-worker** distribution
strategies; Oracle-level parallel tuning over its chief/worker RPC protocol is
not a promise that a multi-worker `distribution_strategy` is supported.

## Route in this order

1. Read [api-reference.md](references/api-reference.md) for the verified
   environment contract, role detection, RPC surface, and reporting semantics.
2. From the skill root, run `python sub-skills/distributed-tuning/scripts/check_distributed_env.py` before importing or constructing a
   distributed tuner. It only inspects environment variables; it never starts
   a server or opens a socket.
3. Follow [workflows.md](references/workflows.md) for the launch sequence,
   shared project directory, status handling, and orderly shutdown.
4. Use [troubleshooting.md](references/troubleshooting.md) for missing
   variables, accidental roles, connection stalls, filesystem divergence, and
   cleanup failures.

## Non-negotiable launch contract

Set all of these together on every participating process:

- `KERASTUNER_ORACLE_IP`: the address used both to bind the chief service and
  to reach it from workers.
- `KERASTUNER_ORACLE_PORT`: the same available TCP port for the chief service.
- `KERASTUNER_TUNER_ID`: a deliberate identifier, unique at the independent
  tuner/group coordination scope.

An ID containing the case-sensitive substring `chief` is treated as the chief
side. The chief starts `OracleServicer`; other IDs construct `OracleClient` and
proxy Oracle calls. A partial environment is invalid: KerasTuner raises
`RuntimeError` when the IP is set without the port or tuner ID. The bundled
checker is intentionally stricter and treats empty/whitespace values as
missing, including port/ID values supplied without an IP; do not bypass this
preflight because runtime role detection is key-presence based.

Use a reachable non-loopback address for different hosts, an open and reserved
port, the same `directory`/`project_name` on a shared writable filesystem, and
an environment where the `grpcio` runtime dependency is installed. The RPC
transport is insecure gRPC, so keep the address on a trusted network or behind
an appropriate network control; this protocol does not provide TLS.

## Role and lifecycle guardrails

- Start the same tuner program with the chief environment on exactly one
  process/group. Its `search()` path saves the Oracle and starts the
  `OracleServicer` server, which otherwise would not block the process.
- Start workers with the same Oracle IP/port and non-chief IDs. Clients wait
  for the chief service with `wait_for_ready=True` for up to 60 minutes per
  RPC; this tolerates startup races but does not repair a wrong address,
  blocked port, or an absent chief.
- Give independent tuner processes/groups distinct IDs. If a training backend
  groups processes into one multi-worker strategy, preserve that backend's
  required ID convention rather than inventing a second Oracle group.
- Keep the project directory shared and writable until all workers have
  finished. Do not let multiple processes independently delete it with
  `overwrite=True`.
- Let workers observe `STOPPED` and exit their search loop; do not kill the
  chief before ongoing trials and registered tuner IDs have drained. The
  chief's server wait loop exits after its stop signal and drain condition.

The test helper `keras_tuner.test_utils.mock_distribute` is evidence for the
environment protocol only. It patches `os.environ`, creates threads, and
picks a port for tests; it is not a production launcher or runtime dependency.

## Verification focus

A useful check must show: an entirely absent environment remains valid ordinary
local mode, no partial environment is accepted as ordinary local mode, and a
complete set is accepted without a socket or server; a chief ID is not confused
with a worker ID; and all participants refer to one reachable endpoint and one
shared project directory. Do not use the mock test helper as proof that a real
cross-host network or filesystem is configured.
