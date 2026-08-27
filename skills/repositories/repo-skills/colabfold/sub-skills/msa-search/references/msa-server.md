# Local MSA Server

A local MSA server is useful when many ColabFold clients need server-style MSA generation without using the public service. It is more operationally complex than `colabfold_search`: setup downloads binaries/databases, configures paths, can require very large memory, and may integrate with system services.

## When to choose a local server

Choose a local API/MSA server when:

- Multiple users or tools need an HTTP API compatible with ColabFold MSA requests.
- You need low-latency repeated searches and can keep database indexes resident in memory.
- Public-server use is inappropriate for privacy, throughput, or policy reasons.
- The environment has operational support for database updates, workers, logs, and restarts.

Prefer plain `colabfold_search` when:

- A single pipeline can run local batch MSA generation from the command line.
- You do not need an HTTP endpoint.
- You cannot allocate server-grade RAM/storage or manage long-running workers.

## Configuration concepts

A typical server configuration contains:

- `server.address`: bind address and port, commonly loopback plus a reverse proxy for TLS/gzip if exposed.
- `server.pathprefix`: API prefix, commonly `/api/`.
- `server.cors`: whether to emit permissive CORS headers.
- `server.dbmanagment`: database-management endpoints; leave disabled unless on a trusted admin-only network.
- Optional `server.auth`: HTTP Basic Auth credentials.
- Optional `server.ratelimit`: token-bucket rate limiting with allowlist support.
- `worker.paralleldatabases`: number of databases searched in parallel; higher values use more CPU.
- `paths.results`: shared job results/scratch directory.
- `paths.mmseqs`: MMseqs2 binary path.
- `paths.colabfold.uniref`: UniRef database basename/path.
- `paths.colabfold.environmental`: environmental database basename/path.
- `paths.colabfold.pdb`: PDB/template search database path.
- `paths.colabfold.pdb70`, `pdbdivided`, `pdbobsolete`: template support paths.
- Optional `paths.colabfold.gpu`: enables GPU mode, gpuserver mode, and device pinning.
- `local.workers`: worker count for single-binary local mode.

Use relative paths only when the server binary documents their resolution. For reproducible operations, prefer explicit absolute server-side paths in the service config, but do not embed machine-local paths in reusable skill content.

## Setup caveats

Treat server setup scripts as reference-only unless the user explicitly approves heavy network and system mutation. A full setup can:

- Check for tools such as `curl`, `aria2c`, `rsync`, and cloud CLIs.
- Download pinned MMseqs2 and server binaries.
- Download UniRef, environmental, PDB, and template databases.
- Compile or install a server binary.
- Start a foreground process or configure `systemd`.
- Require choosing a PDB rsync mirror before template setup.

For quick non-production tests, a mini/debug database mode may exist in server tooling, but do not confuse it with production MSA quality.

## Resource expectations

Operational facts to communicate before planning deployment:

- Full ColabFold databases require hundreds of GB of disk space.
- Server-grade low-latency CPU operation can require roughly 768 GB to 1 TB RAM to keep indexes resident, plus worker memory.
- Batch `colabfold_search` can often skip precomputed indexes, but local server response times depend heavily on resident indexes.
- GPU mode requires compatible MMseqs2-GPU, CUDA drivers/runtime, and GPU-compatible database/index preparation.
- If databases exceed GPU memory, MMseqs2-GPU may stream between host and GPU memory, but performance and stability still depend on host memory and I/O.

## Memory residency

Low-latency CPU server deployments usually preload index files into system cache with a tool such as `vmtouch`. This is an operational step, not a ColabFold runtime requirement for ordinary batch searches.

Example pattern for an operator-owned server host:

```bash
cd /server/databases
sudo vmtouch -f -w -t -l -d -m 1000G *.idx
```

Before suggesting this, confirm the host has enough RAM and that the user accepts privileged cache-pinning operations.

## GPU server block

A GPU configuration can enable:

- `gpu`: MMseqs2-GPU search.
- `server`: GPU server mode to reduce repeated search overhead.
- `devices`: global visible device list.
- Per-database device overrides such as UniRef/environmental/PDB devices for VRAM management.

For command-line `gpuserver` troubleshooting and examples, use [`local-mmseqs-workflows.md`](local-mmseqs-workflows.md).

## Client integration

To use a custom API server from local prediction, pass its URL to ColabFold batch prediction:

```bash
colabfold_batch input_sequences.fasta out_dir --host-url https://msa.example.org
```

Notebook users set the equivalent `host_url` argument in the prediction call.

Validation steps:

- Confirm the endpoint is reachable from the client network.
- Confirm authentication/rate limits are documented for users.
- Run one small protein query before sending a large batch.
- Check server logs for MMseqs2 failures, database path errors, and timeout messages.

## Security cautions

- Do not expose database-management endpoints on an untrusted network.
- Use TLS and authentication if the endpoint is reachable beyond localhost/trusted networks.
- Consider rate limiting; MSA jobs can consume substantial CPU/GPU/RAM.
- Keep job result directories on storage with cleanup policies and appropriate access controls.
