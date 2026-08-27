# Agents and environments

Harbor separates the program that acts from the container/runtime in which it
acts. Resolve both through their factories before spending a trial.

## Agent selection

The run-level agent configuration is an `AgentConfig`:

```yaml
agents:
  - name: codex
    model_name: openai/<model>
    kwargs:
      reasoning_effort: high
    env:
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    n_concurrent: 2
    skills:
      - ./skills/python-style
```

The equivalent CLI is:

```bash
harbor run -p ./tasks/example \
  --agent codex --model openai/<model> \
  --agent-kwarg reasoning_effort=high \
  --agent-env OPENAI_API_KEY="$OPENAI_API_KEY" \
  --skill ./skills/python-style
```

`--agent` accepts a registered built-in name, a custom class import path in
`module.path:ClassName` form, or an ACP registry shorthand such as
`acp:<program>[@version]`. The unified `--agent` option takes precedence over
the deprecated `--agent-import-path`. The factory treats a colon-bearing
`name` as an import path, then constructs the class with a log directory,
`model_name`, configured kwargs, and resolved environment variables. A custom
agent must be importable in the execution environment; merely spelling an
import path is not an integration test.

To discover the installed built-ins, use live help or the installed package's
`AgentName` values rather than copying an old list into a config. Agents differ
in optional dependencies, model endpoint requirements, Windows support,
trajectory loading, native resume, and handoff. Verify those capabilities for
the selected agent before using the related option.

A job may repeat `--model`; each model creates a distinct agent/model cell in
the evaluation matrix. If a config has multiple `agents`, model and agent
identity are preserved in each generated `TrialConfig`. Do not infer that all
agents accept the same kwargs or model naming scheme: use the selected agent's
constructor contract and provider documentation.

Run-time execution-only injection is distinct from task authoring:

- `--agent-env` / `AgentConfig.env` supplies variables to the agent process.
- `--mcp-config` adds MCP server configuration to the agent config.
- `--skill` adds local or git-sourced skill directories. Harbor resolves a git
  source to a cached copy and records skill provenance in the lock.
- `--allow-agent-host` adds run-specific hosts for the agent phase only.
- `--agent-include-logs` and `--agent-exclude-logs` filter downloaded agent
  logs; exclusions win over includes.
- `--extra-instruction-path` and `--extra-instruction` alter the task prompt
  for this run and are recorded in the config.

A task's MCP/server/skill declarations are benchmark inputs and should be
routed to `author-benchmarks`; these run-level options are execution choices.
A simulated user (`--user-agent` plus `--bridge`) is a special nested agent
configuration and requires a bridge. It is not supported for multi-step
trials.

## Environment selection

`EnvironmentConfig` chooses a built-in provider with `type` or a custom
provider with `import_path`:

```yaml
environment:
  type: docker
  force_build: false
  delete: true
  override_cpus: 4
  override_memory_mb: 8192
  extra_allowed_hosts: [pypi.org]
```

The equivalent short form is `--env docker`. `--env module.path:ClassName`
selects a custom environment import path. The current built-in registry
contains local/container and hosted providers including `docker`, `daytona`,
`e2b`, `modal`, `runloop`, `ec2`, `gke`, `openshift`, `novita`, `islo`,
`langsmith`, `tensorlake`, and other installed provider types; the exact set
is version-dependent. Use `harbor run --help` and environment preflight rather
than relying on an old list.

The default type is Docker when neither `type` nor `import_path` is supplied.
The factory lazily imports provider SDKs, so an optional provider can fail with
an actionable extra-dependency message such as `harbor[<provider>]` or
`harbor[cloud]`. A hosted service additionally needs its API key, account,
quota, and provider-specific permissions. Do not claim cloud support was
verified because a provider enum exists.

Before a run, Harbor calls the provider's preflight when available. Run
preflight catches credential/configuration failures before creating trials;
it does not prove that a task image builds or that a model can answer. A safe
provider check is:

```bash
harbor --version
harbor run --help
# Then use --print-config, or a tiny --install-only run, before a full job.
```

For a custom environment, the class must satisfy the `BaseEnvironment` runtime
contract and expose any claimed resource/network capabilities. Implementing or
registering a custom class belongs to `integrations`; selecting an existing
import path for a run belongs here.

## Environment lifecycle

A trial creates the selected environment with task environment settings and
run-level overrides, starts/builds it, calls agent setup, executes the agent,
collects output, runs verification in shared or separate mode, persists the
result, and tears down according to `delete`. A multi-step trial reuses the
same environment across ordered steps. `force_build` controls whether the
provider rebuilds instead of reusing a cached environment.

The environment is also responsible for phase network policy, file uploads and
downloads, service/compose access, health checks, and provider-specific
resource enforcement. Its capabilities determine whether a request is
honorable. Harbor validates capabilities rather than silently weakening the
request.

## Choosing local versus hosted execution

Use Docker first for a small, reproducible local smoke test when Docker and
its required Linux/container features are available. Use a cloud provider when
parallel rollout throughput or provider-specific hardware is required; set
`-n/--n-concurrent` to the desired trial concurrency and confirm provider
limits.

`--launch` is a hosted Harbor job and has separate hosted config/credential
rules. It supports secret grants and `--credential-mode` (gateway or direct)
only in launch mode. `--upload` is a local execution followed by a credentialed
result upload. Keep those modes explicit and never place secret values in job
YAML, command logs, or handoffs.

## Minimal preflight sequence

1. Confirm `harbor --version` and live command help.
2. Resolve exactly one task/dataset source.
3. Run `--print-config`; for launch use `--launch --dry-run`.
4. Confirm agent import/extra, model credential, environment extra/key, task
   OS/backend, resource capability, network capability, and artifact provider
   support.
5. Run a tiny local or `--install-only` check if the user asked for setup
   validation.
6. Only then start the full job or trial.
