# Integration troubleshooting

Diagnose the earliest failing boundary. Do not start a costly trial to learn
whether an import, config, credential, or provider capability is missing.

## Import and factory failures

| Symptom | Likely boundary | Recovery |
|---|---|---|
| `ModuleNotFoundError` for a custom class | Package is not on the Harbor process `sys.path`, or the module path is wrong | Run the same interpreter as `harbor`; import the module, then import the exact `module:ClassName`; package the extension or adjust the environment before a run |
| `Unknown agent type` | `name` is neither a current built-in value, an ACP shorthand, nor a custom import path | Put the full `module:ClassName` in `AgentConfig.import_path` or pass it as the unified agent value; do not invent a registry name |
| `At least one of agent name or import path` | Agent config is empty after CLI/config merge | Set exactly one built-in `name` or custom `import_path`; `AgentConfig` defaults only where the installed model says it does |
| Constructor gets unexpected/missing kwargs | Factory forwards config `kwargs` plus framework values | Inspect the live constructor; accept common framework kwargs and keep extension-specific values under validated `kwargs`; avoid swallowing `TypeError` |
| environment import error suggests an extra | Lazy provider module was selected without its SDK | Install only the named Harbor extra or use a provider already installed; do not claim support from the enum alone |
| environment definition error | Dockerfile/image/Compose/provider definition is incompatible | Validate the task environment and selected provider before changing extension code; a custom provider must implement `_validate_definition()` |

Keep source and installed distribution aligned. A passing import from a source
checkout is not the same as a passing `harbor` entry-point import. Record
`harbor --version`, `python -c 'import harbor; print(harbor.__file__)'`, and the
extension package version in the test report without exposing local machine
paths in the runtime skill.

## Agent lifecycle failures

- **No output or empty context:** the custom `run()` did not populate
  `AgentContext`. Record observations while commands execute and implement
  `populate_context_post_run()` only for logs that are reliably available after
  sync.
- **Permission denied:** the extension assumed root. Use `environment.exec()`
  for the configured default user, `exec_as_root()` only for installed-agent
  system setup, or declare the task's user deliberately.
- **Resume/load fails before execution:** inspect the matching
  `SUPPORTS_RESUME`, `SUPPORTS_LOAD_NATIVE_TRAJECTORY`, or
  `SUPPORTS_LOAD_ATIF_TRAJECTORY` flag. A fresh conversation is not equivalent
  to native resume; do not set the flag merely to bypass preflight.
- **Windows mismatch:** the task's OS is Windows but the agent's
  `SUPPORTS_WINDOWS` or environment capabilities are false. Select a compatible
  pair or change the task target intentionally; do not catch the validation
  error.
- **Bridge rejected:** the target's `SUPPORTED_BRIDGES` does not contain the
  configured bridge, or the target lacks the corresponding protocol mixin.
  Validate built-in targets during job preflight and custom/import-path targets
  during trial setup.
- **Model runs under the wrong endpoint:** inspect `model_connection.provider`,
  `configured_base_url`, and redacted env names. Explicit agent `extra_env`
  wins over ambient variables; do not log `api_key`. Add a `ModelConnectionSpec`
  rather than manually copying every provider key.

## Environment and provider failures

Separate these four questions:

1. **Can the class import?** `EnvironmentFactory` lazy import or custom import
   path.
2. **Can the provider preflight?** SDK, CLI/config, credential/profile, and
   account checks. `EnvironmentFactory.run_preflight()` is the read-only gate
   before trials are queued.
3. **Can the provider enforce the task?** `capabilities` and
   `resource_capabilities()` must cover network mode, allowlist entry types,
   resource policy, GPU/TPU, Windows, mounts, dynamic policy, and Compose.
4. **Can this particular run work?** image build, registry, endpoint,
   provider quota, model key, and task instruction are runtime concerns.

A preflight success answers only question 2. A config parse answers none of
questions 2–4. If the provider cannot enforce `no-network` or `allowlist`, the
base class should reject the task rather than silently run publicly. If a
provider's SDK is absent, do not turn that into a task failure or install the
whole cloud bundle without approval. Docker is a valid fallback only when the
experiment does not require the requested provider semantics.

For cloud failures, preserve the provider error and classify credentials,
network/TLS, account/quota, image, and unsupported task shape separately. Cloud
and live-provider tests are not default CPU verification; mock SDK calls and
run only a tiny explicitly approved smoke test when needed.

## Plugin failures

- `Unknown plugin`: run `harbor plugins list`; entry points use the exact group
  `harbor.plugins`. Or pass a full `module:ClassName`.
- `is not a JobPlugin`: the imported class lacks async `on_job_start` and
  `on_job_end` protocol methods. Subclass `BaseJobPlugin` while developing to
  get the abstract-method gate.
- Constructor `TypeError`: inspect plugin kwargs. CLI `--plugin-kwarg` accepts
  `key=value`; with multiple plugins, prefix a key with the exact plugin value
  (`PLUGIN.key=value`) so it binds unambiguously.
- Hook has no effect: `on_job_start` is called only after a job is created and
  before trials run. Confirm the plugin registered its job/trial hooks and that
  its state is local/testable.
- End hook failure: finalization logs the failure and continues to later
  plugins. Use a deliberate `fail_fast` option only for integrations whose
  contract requires the whole job to fail.

Mock outbound requests and verify hook order with a fake job/result. A plugin
that sends telemetry, creates datasets, uploads artifacts, or changes remote
sessions is credentialed/mutating; import success is not external integration
verification.

## MCP and skills failures

- **Validation says URL/command missing:** match transport to fields:
  `sse`/`streamable-http` need `url`; `stdio` needs `command` and optional
  `args`. Normalize legacy `http` to `streamable-http`.
- **Server disappeared:** inspect task plus runtime merge by server `name`.
  Runtime entries replace task entries with the same name. Check the resolved
  config, not only the input file.
- **Server is configured but tool calls fail:** Harbor's Pydantic validation
  does not probe a URL or install a stdio command. Check service health,
  container DNS, network policy, transport support of the selected agent, and
  command availability inside the environment.
- **Skills are not visible:** every skill source needs a top-level or nested
  `SKILL.md` recognized by the resolver; confirm the resolved source and
  `environment.skills_dir`. An injected destination must be absolute when
  explicitly configured. The agent adapter may copy or discover skills
  differently, so test the chosen adapter rather than assuming universal
  support.
- **Wrong skill wins:** duplicate directory names use later-source precedence;
  preserve order and inspect the job lock digest/provenance.
- **MCP config parser rejects a file:** use JSON, YAML, or TOML mapping form;
  accepted roots are `mcpServers`, `mcp_servers`, or an `environment` mapping.
  Remove unsupported fields and ensure each item is a mapping.

Do not use an external MCP server or network-based skill source in default
extension tests. Use a local stdio fixture, a fake HTTP endpoint, or a small
`SKILL.md` tree.

## Simulated-user failures

- **Prompt template rejected:** required variables are
  `{{ bridge_instructions }}` and `{{ instruction }}`; only those plus optional
  `{{ persona }}` are allowed. A persona file requires the persona slot.
- **User and target install conflict:** both roles share one environment and
  installation prefix. If they are the same named agent, remove the conflicting
  user version pin or match the target version.
- **ACP session does not start:** separate ACPX/Node installation, registry
  resolution, target ACP command, target credentials, and bridge config errors.
  Validate reserved override keys and test the target's ACP command locally
  before adding model calls.
- **Private task leaks:** the target should receive only bridge messages; check
  user prompt construction, logs, skills, environment variables, and exported
  trajectories for accidental instruction/credential exposure.

## Verification stop conditions

Stop and report an unresolved gap when the required Python import, constructor,
config, factory, or CPU contract test fails. Keep optional provider, Docker,
cloud, model, registry, ACPX, GPU, Windows, and external MCP failures as
classified limits unless the requested extension explicitly requires one of
them. Never hide a failure with `--disable-verification`, a provider fallback,
or a broader timeout.
