# Harbor operating architecture

Read this when choosing a route or explaining where a configuration belongs.

## Execution objects

- **Task:** an instruction plus an environment definition and verifier. Its
  `task.toml` can declare an agent timeout/user, environment image/resources/
  network/MCP/skills, verifier mode/environment/artifacts, and optional ordered
  `steps`.
- **Dataset:** a local or registry-backed collection of task packages. A
  manifest records task/file references and digests; a benchmark adapter turns
  an upstream benchmark into this format.
- **Agent:** a program implementing Harbor's agent lifecycle. Built-in names
  include `oracle`, `nop`, `claude-code`, `codex`, `gemini-cli`, `openhands`,
  `terminus-2`, and others that vary by release. Custom implementations use an
  import path and must satisfy the agent contract.
- **Environment:** a container or sandbox provider selected at trial time.
  `docker` is the usual local default; cloud/provider types are optional and
  require their own SDKs, credentials, quotas, and capability support.
- **Verifier:** runs after the agent phase, writes a numeric
  `/logs/verifier/reward.txt` or numeric-object `reward.json`, and may run in
  the agent environment or a separate verifier environment.
- **Trial:** one task × agent/model attempt. It persists resolved config,
  lock/results, agent and verifier logs, artifacts, and trajectory data.
- **Job:** a collection of trials created from datasets, tasks, agents/models,
  and attempts. It schedules trials concurrently and stores a job result.

## Configuration layers

Task-side `TaskConfig` describes the task package. Job-side `JobConfig` selects
one or more datasets/tasks and applies job-level agents, environment/provider,
verifier, metrics, artifacts, timeout multipliers, retries, and concurrency.
`TrialConfig` is the resolved single-trial form. CLI overrides are applied to a
loaded config; inspect the resolved configuration before launching a costly job.

`harbor exec` has a separate `ExecConfig` with required `map.compile`, a map
job, and optional `reduce` task/job. Do not mix its experimental flags/config
with ordinary `harbor run` configuration.

## Result surfaces

Use execution routes to create results. Use analysis routes to inspect
`config.json`, `lock.json`, `result.json`, verifier reward/logs, artifacts,
trajectory files, and retry/cancellation state. Native agent sessions are
agent-specific; ATIF JSON is the portable trajectory format where both source
and target agent support it. Regrade is a verifier-only operation and does not
rerun the agent.

## Phase and capability boundaries

Task environment/network settings provide a baseline. Agent and verifier
settings can override phase policy. A separate verifier needs its own image or
copied top-level environment and explicit artifact transfer. Compose sidecars,
GPU/TPU resources, Windows containers, provider-specific sandboxes, MCP
transports, and model connections are capabilities that must be checked against
the selected backend rather than inferred from a config field.
