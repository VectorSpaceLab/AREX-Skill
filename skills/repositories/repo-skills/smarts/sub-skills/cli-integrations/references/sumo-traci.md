# SUMO and TraCI

SUMO is an optional traffic/map provider. SMARTS's normal local mode starts a
SUMO process and connects through TraCI when a scenario needs SUMO. The
`sumo` extra supplies the Python/binary integration and Rtree performance
support, but it does not make every map valid or guarantee a free port.

## Local mode

The default configuration is:

```text
SMARTS_SUMO_TRACI_SERVE_MODE=local
SMARTS_SUMO_CENTRAL_HOST=localhost
SMARTS_SUMO_CENTRAL_PORT=8619
```

In local mode SMARTS obtains/uses a local SUMO port for each traffic
simulation. A configured `sumo_port` can make port ownership explicit at the
API layer. TraCI startup checks the connection and SUMO version and retries
according to `SMARTS_TRAFFIC_TRACI_RETRIES` (default 5). The version check is
not a substitute for a complete scenario run.

Typical failure clues:

- `SUMO_HOME not set` or a missing `sumolib`/`traci` import means the optional
  SUMO environment is not prepared.
- `sumo`/`sumo-gui` not found means the executable is unavailable even if a
  Python package partially imports.
- `ConnectionRefusedError`, a fatal TraCI error, or a SUMO process that exits
  immediately usually means an invalid map/configuration, incompatible binary,
  or port collision.
- A client connecting to another instance is a concurrency/port ownership
  failure, not a scenario DSL failure.

## Central TraCI mode

Central mode serializes allocation of SUMO server ports through a management
server. This is useful when several SMARTS processes race for ports or when
multiple clients must be coordinated. It is not required for core CLI help and
should be introduced only after a single local case works.

1. Pick a host-visible management port that is free. The package default is
   `8619`; choose a different port for parallel jobs.
2. Start the central server in a dedicated, supervised terminal:

   ```bash
   python -m smarts.core.utils.centralized_traci_server --port 8619 --timeout 600
   ```

   It listens for allocation clients and starts SUMO subprocesses as clients
   request them. It is a long-lived process; do not start it from an import
   probe or leave it unsupervised.
3. In the SMARTS process, select the same host/port and central mode:

   ```bash
   export SMARTS_SUMO_TRACI_SERVE_MODE=central
   export SMARTS_SUMO_CENTRAL_HOST=localhost
   export SMARTS_SUMO_CENTRAL_PORT=8619
   ```

   An engine INI can provide the same `sumo.traci_serve_mode`,
   `sumo.central_host`, and `sumo.central_port` settings. Environment variables
   override the file.
4. Run a bounded experiment, then close the environment and central server.
   Verify the central server's port is released before reusing it.

The central server's `--timeout` only controls idle shutdown; it does not make
SUMO installation, map conversion, or client cleanup automatic. Do not use a
publicly exposed host/port without network controls.

## Port-conflict recovery

For a central-port conflict:

1. Keep the core CLI usable: run `scl --help`, `scl scenario --help`, and
   `scl run --help` in the same environment. These do not need SUMO.
2. Identify the listener with a read-only OS tool (`ss -ltnp`, `lsof -i`, or the
   platform equivalent) and determine whether it is the intended central
   server. Do not kill an unknown process.
3. If the port is owned by an unrelated service, choose a new port and set the
   three `SMARTS_SUMO_*` variables consistently for server and clients.
4. If the server is intended but the client still refuses connection, check
   host/address visibility, firewall/container port mapping, and timeout; then
   retry one client rather than starting duplicate servers.
5. If a SUMO instance owns a per-run TraCI port, stop the owning simulation
   cleanly and verify the port is released. Central mode only manages ports
   through the central server; it does not repair leaked client processes.

For multiple clients, the SUMO/TraCI layer sets a client order and SMARTS uses
retry logic to reduce races. A retry exhaustion error still needs process and
port inspection. The repository's high-parallelism TraCI stress test is not a
safe smoke test and is intentionally skipped here.

## Boundary with scenario and CLI routes

Scenario-studio owns map/traffic DSL and source/generated file layout. This
route owns only the external SUMO prerequisite, server mode, ports, and
failure diagnosis. Do not use `scl scenario build --clean` as a way to repair a
TraCI connection. Build a valid scenario first, then test its SUMO provider in
an isolated run.
