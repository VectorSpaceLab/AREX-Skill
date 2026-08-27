# Runtime Deployment Troubleshooting

Use this when a RocketRide engine cannot start, does not answer `/ping`, rejects
a client, fails through Docker/Helm, or emits no observability data. Start with
low-cost checks and only run heavy build/service commands after the user approves
that action.

## Fast classification

| Symptom | First distinction | Likely owner |
|---|---|---|
| `/ping` fails | Engine not listening, wrong host/port, proxy/firewall, container/cluster routing | Runtime deployment |
| `/ping` works but SDK fails | URI scheme, missing `/task/service`, auth, WebSocket upgrade, SDK config | Runtime deployment + SDK sub-skill |
| Cloud works only with insecure URI or not at all | Wrong Cloud scheme/token | Runtime deployment |
| Local binary exits immediately | Missing Linux runtime libs, wrong working directory, missing `ai/eaas.py`, provider dependency crash | Runtime deployment |
| Source build fails | Missing `pnpm`, compiler/CMake/vcpkg/Java/Tika, download/build state | Development/build/docs or runtime deployment |
| Compose engine cannot reach stores | Container `localhost` misuse, unhealthy dependencies, wrong `.env` | Runtime deployment |
| Helm render/install fails | Missing secrets, invalid values, no external database, chart version/cluster mismatch | Runtime deployment |
| Observability stream is empty | Not subscribed, wrong scope, no trace level for `FLOW`, reconnect lost subscription | Runtime deployment |
| Pipeline starts but provider node fails | Missing provider API key or external service credential in engine environment | Pipeline/nodes plus runtime deployment |

## Endpoint and URI diagnostics

### Health check does not respond

Run the health check from the same network namespace/path as the client:

```bash
curl -v http://<host>:5565/ping
```

If it fails:

1. Confirm the engine process or container/pod is running.
2. Confirm it is bound to the expected interface:
   - `--host=127.0.0.1` is local-only.
   - `--host=0.0.0.0` listens on all interfaces but must be protected.
3. Confirm the host port is actually `5565` or the configured mapped port.
4. Check firewall, Docker port mapping, Kubernetes Service/port-forward, or
   ingress rules.
5. For release archives, start from the runtime directory so `./ai/eaas.py`
   resolves.

Do not debug SDK code until `/ping` works on the intended path.

### `/ping` works but task execution fails

The health endpoint is HTTP. Task traffic is WebSocket:

```text
ws://<host>:5565/task/service
```

Check:

- Did the client use a base URI that normalizes correctly to `/task/service`?
- Is a proxy or ingress allowing WebSocket upgrade headers and long-lived
  connections?
- Is the endpoint Cloud (`https://api.rocketride.ai`) or local (`ws://host:5565`)?
- Is the first WebSocket frame authenticated with `ROCKETRIDE_AUTH` or
  `ROCKETRIDE_APIKEY` when required?
- Is the client accidentally using `localhost` from inside a container, where it
  refers to the container itself instead of the host or engine service?

### URI normalization versus engine-not-listening case

Use this sequence for the difficult failure where a user reports a connection
error but the root cause is unclear:

1. `curl http://<host>:5565/ping`
   - Fails: treat as engine/listening/networking.
   - Succeeds: continue.
2. Confirm the task socket should be `ws://<host>:5565/task/service`.
3. If target is Cloud, replace local-style schemes with:
   `ROCKETRIDE_URI=https://api.rocketride.ai` and token auth.
4. If target is Docker/Kubernetes, test from both host and in-network contexts:
   host uses published/forwarded ports; containers/pods use service names.
5. If WebSocket opens and then fails, inspect auth and task command responses.

## Release archive startup failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `./engine: No such file or directory` | Wrong platform archive or not in runtime directory | Use matching OS/arch asset; `cd` to extracted runtime directory |
| `error while loading shared libraries: libc++.so.1` or similar | Missing Linux runtime libraries | Install `libc++`, `libc++abi`, and `libgomp` package names for the distro |
| `ai/eaas.py` not found | Started from wrong working directory | Run `./engine ./ai/eaas.py ...` from the runtime directory |
| Port already in use | Another engine/process uses `5565` | Stop the old process or use a different exposed port/proxy |
| Works locally but not remotely | Bound to loopback or firewall blocks port | Use the intended `--host` and network policy; add TLS/auth before exposure |

Linux package names:

```bash
# Debian / Ubuntu
sudo apt install libc++1 libc++abi1 libgomp1

# Fedora / RHEL
sudo dnf install libcxx libcxxabi libgomp

# Alpine
sudo apk add libc++ libgomp
```

## Source build/runtime failures

Source builds are heavy. For a user who only needs to run RocketRide, prefer a
release archive or an existing container image. If source build is required,
classify failures by phase:

| Phase | Signal | Fix direction |
|---|---|---|
| Workspace install | `pnpm` missing or workspace install fails | Install/enable pnpm and rerun install; do not assume server code is broken |
| Download/fetch | Cannot fetch release asset/manifest | Retry network/proxy or force local compile if intended |
| Configure | CMake/vcpkg/compiler errors | Install compiler/toolchain; rerun configure/build task |
| Runtime staging | Missing Python/JRE/Tika/runtime libs | Re-run server build/setup tasks; check build state |
| Module sync | Nodes/AI/client modules missing from runtime | Re-run `server:build` rather than starting `engine` from a partial dist |
| Tests | Engine test failures | Treat separately from deployment smoke; tests are heavier than `/ping` |

Recognize these task meanings:

- `server:build`: assemble runtime; may download or compile.
- `server:run`: assemble then start a long-running engine.
- `server:dev`: start engine plus development shell.
- `server:package`: create release archive; requires prior build state.
- `server:test`: build and run tests; not needed for a simple health check.

## Auth and secret failures

| Symptom | Likely cause | Fix |
|---|---|---|
| Cloud client rejected | Missing/invalid token | Set `ROCKETRIDE_AUTH` or `ROCKETRIDE_APIKEY` |
| Cloud URI uses `http://` or `ws://` | Insecure scheme | Use `https://api.rocketride.ai` or `wss://...` |
| Local exposed engine accepts unauthenticated clients | Development-style local config used in production | Put behind TLS/auth and require an API key |
| Provider node errors at runtime | Provider key absent from engine environment | Add provider env var/Secret; reference it from pipeline config |
| Secret appears in `.pipe` | Literal credential committed to pipeline JSON | Replace with environment placeholder and rotate the leaked credential |
| Kubernetes pod does not roll after external secret rotation | Secret name unchanged and checksum not bumped | Update `engine.existingSecretChecksum` |

Keep three credential classes separate:

1. RocketRide engine auth: `ROCKETRIDE_AUTH` / `ROCKETRIDE_APIKEY`.
2. Provider API keys: OpenAI, Anthropic, Hugging Face, Gemini, Ollama host, etc.
3. Infrastructure credentials: PostgreSQL, Chroma, Milvus/MinIO, object stores.

## Docker Compose failures

### Engine cannot reach PostgreSQL/vector stores

Inside the Compose network, `localhost` means the current container. The engine
should use Compose service names:

- `postgres:5432`
- `milvus:19530`
- `chroma:8000`

The Compose stack builds `POSTGRES_URL` for the engine. If it was overridden,
verify it uses service names, not host-only addresses.

### Vector-store behavior is confusing

The engine requires PostgreSQL/pgvector. Milvus and Chroma are optional vector
stores that may only fail when a pipeline node tries to use them. Check:

```bash
docker compose ps
docker compose logs -f engine
docker compose logs -f postgres
docker compose logs -f milvus
docker compose logs -f chroma
```

If a local development override is changing behavior, compare with a run that
uses only the base Compose file.

### Host cannot reach engine

Check the `ENGINE_PORT` mapping. From the host, use the published port:

```bash
curl http://localhost:${ENGINE_PORT:-5565}/ping
```

From another container on the same network, use:

```text
ws://engine:5565/task/service
```

### Persistent state is stale

Named volumes keep database/vector-store state. If the user explicitly wants a
fresh stack and accepts data deletion:

```bash
docker compose down -v
```

Do not remove volumes when preserving user data matters.

## Helm/Kubernetes failures

### Render/install fails with missing secrets

The chart intentionally fails if neither chart-managed nor external secrets are
configured. Set one of:

```yaml
engine:
  secrets:
    OPENAI_API_KEY: "sk-..."
    POSTGRES_PASSWORD: "change-me"
```

or:

```yaml
engine:
  existingSecret: "rocketride-credentials"
  existingSecretChecksum: "rotation-marker"
```

### Pod starts but is not ready

Read the probes and logs:

```bash
kubectl -n <namespace> get pods,svc
kubectl -n <namespace> describe pod <engine-pod>
kubectl -n <namespace> logs <engine-pod>
```

Then test `/ping` through the same service path clients will use:

```bash
kubectl -n <namespace> port-forward svc/<release-fullname>-engine 5565:5565
curl http://127.0.0.1:5565/ping
```

If the pod starts but pipelines fail, verify external PostgreSQL, vector stores,
and provider secrets before changing client code.

### Ingress works for `/ping` but not task runs

Likely WebSocket upgrade or timeout handling. Ensure the ingress controller:

- preserves `Upgrade` and `Connection` headers,
- allows long-lived WebSocket connections,
- routes `/task/service` to the engine service,
- terminates TLS correctly when clients use `https://` or `wss://`.

### GPU pod does not schedule

GPU values require cluster prerequisites:

- NVIDIA drivers or GPU Operator on nodes,
- NVIDIA device plugin,
- matching `nodeSelector` labels,
- tolerations for GPU taints,
- `nvidia.com/gpu` resource availability.

Disable CPU/memory HPA for GPU inference scaling and use a GPU-aware scaler such
as KEDA with DCGM/Prometheus or queue-depth metrics.

## Observability failures

| Symptom | Cause | Fix |
|---|---|---|
| No events after reconnect | Subscriptions are per connection | Resubscribe after reconnect |
| No `FLOW` events | Pipeline started with trace level `none` | Start with `pipelineTraceLevel: "summary"` or higher |
| Only current status, no history | Runtime has no durable event database | Persist events in your subscriber |
| Missing other user's dev run | Scope only covers tasks owned by your token | Use the correct token/scope; team deployed runs need `teamId` |
| Old errors disappeared from status | Snapshot keeps only recent entries | Subscribe and persist events live |
| Dashboard ordering ambiguous | No global event id | Order by connection-local `seq` and correlate by task/project/source |

Use `TASK` and `SUMMARY` for basic dashboards. Add `FLOW` only when the run was
started with an appropriate trace level. Add `OUTPUT` for engine log lines and
`SSE` for node-emitted UI messages.

## Provider and database runtime failures

A successful `/ping` only proves the engine is alive. It does not prove provider
keys, external model endpoints, vector stores, or object stores are configured.
When a pipeline fails after start:

1. Identify the node/provider that failed.
2. Check whether its key/host is expected in the engine environment.
3. Confirm Docker/Helm injected the variable into the engine process or pod.
4. Replace any literal secret in pipeline JSON with an environment placeholder.
5. Check network reachability from the engine runtime, not from the user's shell.

Route detailed node config/schema questions to the node catalog sub-skill and
pipeline shape questions to the pipeline-authoring sub-skill.
