---
name: integrations
description: "Extend Harbor with custom agents, environments, plugins, bridges,
  model connections, MCP/skills, simulated users, and optional first-party
  integrations; verify extension contracts without invoking external services by
  accident."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Extend Harbor integrations

Use this skill when the requested change is **framework extension work**: a
custom agent or environment, an import-path integration, a job plugin, a model
connection, an ACP/bridge adapter, MCP or injected skills support, a simulated
user, or an optional provider such as LangSmith. Keep the extension self-
contained and prove its contract with mocked or local tests before attempting a
real provider, model, Docker daemon, or network service.

## Route before editing

- **Run an existing task/dataset or select an agent/model/provider:** route to
  [`run-evaluate`](../run-evaluate/SKILL.md). Passing an already implemented
  custom import path to a run is execution work there.
- **Author a task-side MCP declaration, verifier, RewardKit criterion, or
  benchmark package:** route to
  [`author-benchmarks`](../author-benchmarks/SKILL.md). Implementing the MCP
  server, bridge, or framework adapter stays here.
- **Inspect, compare, or publish completed results:** route to
  [`analyze-publish`](../analyze-publish/SKILL.md); do not add result
  interpretation to this skill.
- **Experimental map/reduce execution:** route to
  [`exec-map-reduce`](../exec-map-reduce/SKILL.md).

Read the focused references in this order:

1. [`extension-contracts.md`](references/extension-contracts.md)
2. [`optional-integrations.md`](references/optional-integrations.md)
3. [`mcp-skills-bridges.md`](references/mcp-skills-bridges.md)
4. [`troubleshooting.md`](references/troubleshooting.md)

## Safe extension workflow

1. **Normalize the extension boundary.** Record the target class, public
   import path, lifecycle owner, configuration fields, supported operating
   systems/backends, credentials, and a CPU/local acceptance test. Decide
   whether the work is an external agent, installed agent, environment,
   `JobPlugin`, bridge, or configuration-only adapter.
2. **Check the installed surface first.** Run `harbor --version` and inspect
   the relevant `--help` output. In Python, inspect the installed
   `BaseAgent`, `BaseInstalledAgent`, `BaseEnvironment`, `AgentFactory`, and
   `EnvironmentFactory` signatures. The source checkout and installed
   distribution can differ; record the version used for verification.
3. **Implement through a public contract.** Use `module.path:ClassName` for a
   custom `AgentConfig.import_path` or `EnvironmentConfig.import_path`. Do not
   edit the built-in name/type registries unless the extension is intentionally
   first-party. A custom class is instantiated by the factory with framework
   constructor arguments plus `kwargs`; reject unknown or unsafe options
   clearly.
4. **Respect lifecycle and capability gates.** Agents must populate
   `AgentContext` during `run`; environments must enforce or reject resource,
   network, OS, and compose requirements. Advertise `SUPPORTS_WINDOWS`, resume,
   trajectory, handoff, ATIF, and `SUPPORTED_BRIDGES` accurately. A missing
   capability must fail during preflight, not after a costly run starts.
5. **Separate optional layers.** Import only the selected provider/plugin
   extra. Run provider `preflight()` before queueing trials and distinguish a
   missing SDK from missing credentials, a bad endpoint, and a service failure.
   Never use `harbor[cloud]` or a real API as a substitute for a narrow import
   or mocked contract test.
6. **Resolve configuration before execution.** Validate agent/environment
   config, import the class, merge task and runtime MCP servers by name, resolve
   skills and their destination, and validate bridge target support. Show the
   resulting provider/model/environment and credential gates before a real run.
7. **Test in layers.** Start with import and constructor tests, then factory
   wiring, config validation, lifecycle tests using fake environments, optional
   provider tests with SDK/network calls mocked, and only then an explicitly
   approved end-to-end smoke test. Do not put tests, logs, credentials, or
   generated reports in this runtime skill directory.

## Minimal contracts

An external custom agent subclasses `harbor.agents.base.BaseAgent` and provides
`name()`, `version()`, `async setup(environment)`, and `async run(instruction,
environment, context)`. Its constructor should accept the framework's
`logs_dir` and `model_name` and forward supported common kwargs to `super()`.
Use `environment.exec()` with the configured default user; do not assume root.

An installed agent subclasses
`harbor.agents.installed.base.BaseInstalledAgent`. Add `install(environment)`
for tool setup, use the base execution helpers, and decorate prompt-aware
`run()` methods with `with_prompt_template` when appropriate. Declare native
configuration, model connection, system packages, error patterns, and
trajectory capabilities instead of hiding them in arbitrary CLI code.

An environment subclasses `harbor.environments.base.BaseEnvironment`. Implement
`type()`, `_validate_definition()`, `start(force_build)`, `stop(delete)`,
`upload_file`, `upload_dir`, `download_file`, `download_dir`, and `exec`;
override `capabilities`, `resource_capabilities()`, and `preflight()` when the
provider supports those surfaces. A custom environment can use an arbitrary
string from `type()` and `EnvironmentConfig.import_path`, so it does not need a
new enum member.

A job plugin is a class satisfying
`harbor.models.job.plugin.JobPlugin` (or subclassing `BaseJobPlugin`) with
`async on_job_start(job)` and `async on_job_end(job_result)`. Register a package
under the `harbor.plugins` entry-point group to allow a short plugin name, or
pass its full `module:ClassName` import path. Plugins are attached at job
start; their external mutations and credentials require explicit approval.

Model connections are declarative. An installed agent may set a
`ModelConnectionSpec` with a fixed/default provider, agent-specific key and
base-URL environment names, and optional provider-variable passthrough. The
resolver derives a provider from `model_name` when needed, honors explicit
agent environment values over ambient values, and only exposes selected
variables to the agent. A model string or parsed connection is not proof that
credentials or an endpoint are usable.

MCP servers, skills, ACP, simulated users, RewardKit, and LangSmith have
additional data and lifecycle rules; use the bundled references rather than
copying agent-specific setup commands into a new extension.

## Completion record

Report the files changed, installed version and signatures checked, import and
config tests run, optional backends/services not exercised, and unresolved
capability or credential limits. Do not claim an extension is provider-ready,
Windows-compatible, resumable, ACP-compatible, or model-connected unless that
specific gate was checked.
