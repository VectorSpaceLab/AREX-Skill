# Resources, network, instructions, and artifacts

Execution configuration is layered across task definition, job/trial config,
and CLI overrides. This reference covers the parts that most often change
provider behavior or the evidence available to a verifier.

## Timeouts and resources

Task authors declare environment resources in the task's environment section:

```toml
[environment]
cpus = 2
memory_mb = 4096
storage_mb = 10240
gpus = 1

[environment.tpu]
type = "v6e"
topology = "2x4"
```

These fields are optional. An omitted value uses provider defaults; Harbor does
not invent a task resource request. Separate verifier environments may declare
their own resources.

At run time, CPU and memory have independent enforcement policies:

- `auto`: provider default behavior.
- `limit`: hard ceiling; requires a declared value.
- `request`: reservation only; requires a declared value.
- `guarantee`: reservation and hard ceiling; requires a declared value.
- `ignore`: do not pass the task value to the provider.

Set policies with `--cpus` / `--memory`, or with
`cpu_enforcement_policy` / `memory_enforcement_policy` in job/trial
`environment` config. Run-time value overrides replace task values:

```bash
harbor run -p ./tasks/gpu-task -a <agent> -m <model> -e modal \
  --cpus guarantee --memory request \
  --override-cpus 4 --override-memory-mb 16384 --override-gpus 1
```

`--override-storage-mb` and `--override-tpu TYPE=TOPOLOGY` are also available.
Storage, GPU, and TPU requests are passed through only when the provider
supports them. Harbor validates provider resource capabilities and rejects an
unsupported policy/request instead of quietly running with weaker semantics.
The selected task OS, compose mode, and provider can further constrain GPU,
TPU, Windows, or network support.

Timeout values may come from task-level agent/verifier/environment settings,
trial/job explicit seconds, and multipliers. Specific timeout overrides take
precedence over a general multiplier, and max timeout fields cap effective
values. Job-level multipliers apply to trials; trial-level overrides apply to
that trial. Phase-specific multipliers (`agent_timeout_multiplier`,
`verifier_timeout_multiplier`, `agent_setup_timeout_multiplier`, and
environment build multiplier) take precedence over `timeout_multiplier`.
Use explicit seconds when a synthetic case requires a clear bound:

```bash
harbor trial start -p ./tasks/example -a <agent> -m <model> \
  --agent-timeout 120 --verifier-timeout 30
```

A timeout or missing credential is an execution failure, not evidence that a
larger timeout or verification disable is correct. Change the experiment only
with user approval.

## Network policy phases

Task network configuration has a baseline and optional phase overrides:

```toml
[environment]
network_mode = "public"       # baseline at environment start

[agent]
network_mode = "allowlist"    # only during agent.run()
allowed_hosts = ["api.example.com"]

[verifier]
network_mode = "no-network"   # only during verifier.verify()
```

The supported modes are:

- `public`: full network access.
- `no-network`: no egress.
- `allowlist`: only `allowed_hosts`; an empty/omitted list denies egress.

Allowlist entries are exact hostnames, IPv4/IPv6 literals, CIDRs, or supported
leading-wildcard hostnames. They are not URLs, ports, paths, or bracketed IPv6
values. A bare hostname is exact; include both an apex and wildcard when both
are needed and the provider supports it.

`[environment]` is the baseline for the started agent environment.
`[agent]` and `[verifier]` are phase overrides and require the environment's
`dynamic_network_policy` capability when they differ from the baseline. A
separate verifier uses `[verifier.environment]` as its own startup baseline,
which avoids requiring runtime switching between agent and verifier sandboxes.
Multi-step tasks can override the same fields per step.

Run-level host flags merge only for their intended phase:

- `--allow-environment-host HOST` extends the environment baseline and is
  available while agent setup/build/start may need that host.
- `--allow-agent-host HOST` extends the agent-run allowlist only.

On a `public` baseline these flags do not make the network more restrictive and
may be ignored with a warning. On a restricted baseline they must be valid for
the provider. If a provider cannot enforce a requested mode, dynamic override,
address class, or compose combination, stop before the trial; do not silently
fall back to public networking. Provider support varies, and Windows Docker
containers do not provide the Linux egress-control modes.

Verifier environment mode matters: a shared verifier runs in the agent
environment after the agent phase, while a separate verifier has its own
sandbox and must receive any evidence through artifacts. Keep network policy
and verifier mode aligned with the threat model and the task's declared
inputs.

## Extra instructions, MCP, skills, and log selection

Job/trial `extra_instruction_paths` are read and appended before inline
`extra_instructions`; CLI `--extra-instruction-path` and
`--extra-instruction` follow the same order. They change the instruction
without modifying the task source. Record the resolved values when comparing
runs.

`--mcp-config` may be repeated and loads a Claude-style or Harbor MCP config
for the agent. `--skill` may be repeated for local paths or git sources; skill
content is copied into the sandbox and its resolved provenance is locked.
These are agent inputs, not verifier artifacts. Route task-declared MCP/skill
contracts to `author-benchmarks`; route custom server/bridge implementation to
`integrations`.

`include_logs` and `exclude_logs` on the agent/verifier config control which
log files are downloaded. If includes are present, only matching files are
kept; excludes are applied afterward and win on overlap. The reward file is
kept for verifier logs even when verifier include filtering is used.

## Artifact collection

The convention directory `/logs/artifacts/` is collected automatically. On a
local mounted environment it is already visible on the host; on remote
providers Harbor downloads it after the trial. The conventional host location
is:

```text
<trial-dir>/artifacts/logs/artifacts/
```

Use `artifacts` for arbitrary paths. String entries mirror the absolute source
under the trial's flat artifacts root:

```yaml
artifacts:
  - /app/output.csv
  - /workspace/results
```

Object entries control host placement or a compose sidecar source:

```yaml
artifacts:
  - source: /app/answer.json
    destination: answers/final.json
  - source: /var/log/api/requests.log
    service: api
```

`source` is an absolute path in the service and is also the path at which the
file is recreated inside a separate verifier. `destination` is only a
relative host path under `<trial-dir>/artifacts`; it cannot contain `..` or
shadow `manifest.json`. `service` defaults to the main agent service and
requires a compose-capable provider when it names a sidecar.

Collection is best-effort: an unavailable path records a failed manifest entry
rather than failing the trial. The flat artifact root is shared by services;
source-path overlaps can collide. The first claimant is retained and later
entries are recorded as skipped, so avoid equal or nested source paths across
services. `manifest.json` records source, destination, service, type, and
status. Inspect it before relying on evidence or attempting a regrade.

Collection phases are ordered to preserve evidence: main collect hooks, main
artifacts, optional main stop for a final separate verifier, sidecar collect
hooks, sidecar artifacts, then manifest. Sidecar artifacts can carry evidence
from a service the main agent cannot write to; however, intermediate multi-step
snapshots occur while later steps still need the main service. Put tamper-
sensitive sidecar evidence on the final step or a single-step separate-
verifier task.

In separate verifier mode, configured artifacts are uploaded back to their
original `source` paths (the host `destination` is not used as an in-container
path). Missing/failed/skipped artifacts make a source unsuitable for regrade.
Artifacts are also how a verifier reads trajectory or generated output that is
not implicitly transferred; `/logs/agent` and `/logs/verifier` are not copied
unless explicitly declared.
