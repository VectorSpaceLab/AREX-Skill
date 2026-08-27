# Harbor task format

This reference is a self-contained authoring contract. It describes the current
Harbor task model without depending on a checkout path.

## 1. Scaffold and inspect

Use a package name in `org/name` form:

```bash
harbor task init "org/task-name" --description "Short task description"
# Current CLI also supports:
harbor init --task "org/task-name" --output-dir path/to/tasks
harbor task init "org/multi-step" --steps 2
```

A normal task has:

```text
task-name/
├── task.toml
├── instruction.md
├── README.md                 # human maintenance/documentation
├── environment/
│   ├── Dockerfile            # or docker-compose.yaml, or runtime files
│   └── ...
├── solution/                 # optional; used by the Oracle agent
│   └── solve.sh              # solve.bat for Windows
└── tests/
    ├── test.sh               # test.bat for Windows
    └── ...
```

Harbor accepts a pre-built image through `environment.docker_image`; a
Dockerfile is then optional. If no Dockerfile or Compose file is present,
other files in `environment/` are uploaded as runtime files by supported
environments. Do not assume every cloud provider supports Compose.

Scaffolding is not verification. Inspect the generated files, replace
placeholder instructions/tests, and parse the final TOML before starting any
environment.

## 2. `task.toml` identity and metadata

Use the current schema marker and a registry identity:

```toml
schema_version = "1.4"

[task]
name = "org/task-name"
version = "1.0.0"
description = "A short, observable task goal"
authors = [{ name = "Author", email = "author@example.invalid" }]
keywords = ["python", "files", "pytest"]

[metadata]
difficulty = "medium"
category = "programming"
tags = ["...", "...]
```

`[task].name` is package identity, not merely the directory name. It must be a
valid `org/name` identifier and should remain stable across adapter runs.
`version` is the task package version; it is distinct from the top-level
`schema_version`. Populate keywords with a small, searchable set including
domain and verifier style. Metadata is arbitrary and should not be used to
hide required config.

## 3. Instruction, environment, solution, tests

`instruction.md` is the agent-facing request. State:

- the goal and expected output paths/formats;
- relevant constraints, allowed tools, and success behavior;
- what may be modified and what must be preserved.

Do not include the test source, exact expected answer, reference solution,
hidden grader inputs, or a canary/answer string. A task must be solvable from
the instruction and environment without reading the verifier implementation.

The environment definition installs dependencies required by the task, not the
solution. Use a pinned base image when reproducibility matters, set a sensible
`WORKDIR`, and remove package-manager caches when practical. The default Linux
special paths are:

- `/tests/` — verifier files;
- `/solution/` — Oracle solution files;
- `/logs/verifier/` — reward and verifier logs;
- `/logs/agent/` — agent logs/trajectory when explicitly produced.

Windows tasks set `[environment].os = "windows"` and use `solve.bat` and
`test.bat`; do not claim Windows support from a Linux-only smoke test.

The optional `solution/solve.sh` is copied to `/solution` by the Oracle agent.
It is a solvability check, not an answer source for the evaluated agent. The
required Linux verifier entrypoint is `tests/test.sh` (or `test.bat` for
Windows). It should use absolute container paths, return a useful exit status,
and write a numeric reward file even when the test command fails.

## 4. Resources and network policy

All resource requests are optional; omission leaves sizing to the provider:

```toml
[environment]
cpus = 2
memory_mb = 4096
storage_mb = 10240
gpus = 0
gpu_types = ["H100", "A100"]

[environment.tpu]
type = "v6e"
topology = "2x4"
```

TPU topology dimensions are positive integers separated by `x`; chip count is
the product. GPU/TPU claims are provider- and host-dependent.

Network is layered:

```toml
[environment]                 # baseline at environment start
network_mode = "no-network"

[agent]                       # optional run-phase override
network_mode = "allowlist"
allowed_hosts = ["api.example.com"]

[verifier]                    # optional verify-phase override
network_mode = "no-network"
```

Modes are `public`, `no-network`, and `allowlist`. Bare hosts are exact;
leading wildcards, IP literals, and CIDRs depend on provider capability.
Entries are not URLs, ports, or paths. A phase override differing from the
baseline requires `dynamic_network_policy`; otherwise prefer separate
verifier/environment baselines. Run-time host flags are execution concerns,
not task-definition replacements.

## 5. MCP, skills, healthchecks, and artifacts

MCP entries are task-side declarations for compatible agents:

```toml
[[environment.mcp_servers]]
name = "local-tools"
transport = "stdio"
command = "python"
args = ["/opt/tools/server.py"]

# HTTP transports require url instead:
# transport = "sse" or "streamable-http"
# url = "http://service:8000/mcp"

[environment.healthcheck]
command = "test -f /tmp/ready"
interval_sec = 5.0
timeout_sec = 30.0
start_period_sec = 0.0
retries = 3
```

`environment.skills_dir` copies task-provided skills into the agent's skills
configuration. It does not implement a skill system or install an agent
plugin. Route those implementation concerns to `integrations`.

Artifacts are paths intentionally exported from the environment:

```toml
artifacts = [
  "/app/output.json",
  { source = "/app/logs", destination = "logs", exclude = ["*.tmp"] },
]
```

`source` is a container path and cannot contain `..`. `destination` is a
relative path under the trial artifact directory, uses `/`, cannot contain
`..`, and cannot be `manifest.json`. Entries are collected after verification.
For Compose sidecars:

```toml
artifacts = [
  { source = "/var/log/service/requests.json", service = "api" },
]

[[verifier.collect]]
service = "database"
command = "pg_dump -U postgres app > /tmp/app.sql"
timeout_sec = 60.0

# Then collect it from that service:
# artifacts = [{ source = "/tmp/app.sql", service = "database" }]
```

Sidecar source paths must be absolute and sidecar/host artifact entries must not
overlap. Keep sidecar collection commands POSIX-compatible unless invoking a
known shell explicitly.

## 6. Separate verifier and multi-step tasks

The default verifier is shared with the agent container. To isolate grading:

```toml
[verifier]
environment_mode = "separate"

[verifier.environment]
docker_image = "grading-image:tag"
network_mode = "no-network"
```

When a separate verifier is used, the verifier image must contain its own
`/tests/test.sh` or `/tests/test.bat`; tests are not uploaded at runtime. Only
`/logs/artifacts/` and configured artifacts are transferred into the verifier,
at their original absolute paths. Artifacts are therefore the explicit bridge
between an agent environment and a clean grader.

A multi-step task shares one environment but uses ordered `steps/<name>/`
directories:

```toml
multi_step_reward_strategy = "mean"  # or "final"

[[steps]]
name = "scaffold"
min_reward = 1.0
[steps.agent]
timeout_sec = 60.0
[steps.verifier]
timeout_sec = 30.0
artifacts = ["/app/state.json"]
```

Each step may have `instruction.md`, `workdir/`, optional reserved
`workdir/setup.sh`, `tests/`, and `solution/`. Setup runs before the agent and a
non-zero exit aborts the step. Files persist across steps. Scalar `min_reward`
gates the conventional `reward` key; a mapping gates named reward keys and
missing keys fail the gate. `mean` computes per-key means across steps that
produced results; `final` keeps the final step's result. A run-level
`--resume-trajectory` is not a task field and should only be discussed as an
evaluation choice.

## 7. Preflight checklist

Before any container or agent run:

1. Parse `task.toml` with Harbor's `TaskConfig` or the CLI.
2. Confirm package name, schema marker, timeouts, resources, and policy fields.
3. Confirm an OS-appropriate test script and that it writes a reward file.
4. Check artifact paths/destinations for collisions and verifier transfer needs.
5. Check separate-verifier image ownership of `/tests/test.sh`.
6. Check that the Dockerfile does not install the solution or expose the rubric.
7. Use `harbor check <task-dir>` when available; do not use the removed
   `harbor task check` spelling.
8. Run only tiny fixture/help/parser checks unless execution has been approved.

A successful parse or structure check does not establish Docker, Compose, GPU,
Windows, provider, or model/API viability.
