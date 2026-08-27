# Extension contracts

This reference covers framework extension code, not ordinary job invocation.
Verify the installed Harbor version before relying on a signature; the current
CPU inspection surface is Python 3.12+ and the public modules below.

## Custom agents

### External agent

Import from `harbor.agents.base` and subclass `BaseAgent`. The live constructor
accepts `logs_dir`, optional `model_name` and `logger`, task/runtime
`mcp_servers`, `skills_dir`, `extra_env`, an optional `load_trajectory`, and
framework-compatible extra arguments. The class contract is:

```python
from harbor.agents.base import BaseAgent

class ExternalAgent(BaseAgent):
    @staticmethod
    def name() -> str:
        return "external-agent"

    def version(self) -> str | None:
        return "0.1.0"

    async def setup(self, environment) -> None:
        # Install or configure only what the selected environment needs.
        return None

    async def run(self, instruction, environment, context) -> None:
        result = await environment.exec(command="...")
        # Add observations, commands, errors, or metadata to context as the
        # agent works; do not wait until a timeout has discarded the evidence.
```

The abstract methods are `name()`, `version()`, `setup(environment)`, and
`run(instruction, environment, context)`. `resume()` and `load()` default to a
clear `NotImplementedError`; implement them only when native session behavior
is real. Implement classmethod `handoff(trial_dir, cwd)` only when a finished
trial can be resumed by the local CLI. Set these flags deliberately:

- `SUPPORTS_ATIF` for native ATIF trajectory production.
- `SUPPORTS_RESUME` for lossless native multi-step continuation.
- `SUPPORTS_LOAD_NATIVE_TRAJECTORY` and
  `SUPPORTS_LOAD_ATIF_TRAJECTORY` independently.
- `SUPPORTS_HANDOFF` for local post-trial session handoff.
- `SUPPORTS_CONFIG` for the installed-agent configuration path.
- `SUPPORTS_WINDOWS` only if setup and execution work in Windows containers.
- `MODEL_CONNECTION` when the agent has a declarative credential/endpoint
  mapping.
- `SUPPORTED_BRIDGES` only for bridges the agent really implements.

Use the environment's `default_user`: an unqualified `environment.exec()` call
runs as that user. Do not write a custom agent that silently requires root,
network, a particular shell, or a mounted host filesystem. Forward common
constructor arguments to `BaseAgent` so MCP, skills, extra environment, and
trajectory loading are not dropped.

### Installed agent

Subclass `harbor.agents.installed.base.BaseInstalledAgent` when the agent is
installed and run inside the task environment. Implement `install(environment)`
for prerequisites and a `run()` method; use the base helpers
`exec_as_root()` for system packages and `exec_as_agent()` for user-level
installation or execution. The base class provides declarative `CLI_FLAGS`,
`ENV_VARS`, `SYSTEM_PACKAGES`, error classification, prompt-template support,
and installed-agent lifecycle handling. Use `with_prompt_template` if
instruction rendering is part of the contract. Keep provider-specific API
errors distinct so retry policy cannot mistake authentication, model-not-found,
context-window, or safety refusal errors for transient overload.

A custom install method is not a license to invoke package managers in unit
verification. Test the command construction and error paths with a fake
`BaseEnvironment`; gate real installation behind an explicit runtime smoke test.

## Factories and import paths

The factories are lazy and use `module.path:ClassName` import paths:

```python
from harbor.agents.factory import AgentFactory
from harbor.models.trial.config import AgentConfig

config = AgentConfig(
    import_path="my_package.agents:ExternalAgent",
    model_name="provider/model",
    kwargs={"option": "value"},
)
agent = AgentFactory.create_agent_from_config(config, logs_dir=logs_dir)
```

`AgentFactory.create_agent_from_import_path(import_path, logs_dir,
model_name=None, **kwargs)` imports the class and constructs it. In a config,
`import_path` is preferred, but a `name` containing `:` is also treated as an
import path unless it is ACP registry shorthand. A valid built-in `name` uses
the `AgentName` registry; an unknown name is an error. The configured `env` is
resolved and passed as `extra_env`; `kwargs` are constructor kwargs.

For environments, import from `harbor.environments.base` and use:

```python
from harbor.environments.factory import EnvironmentFactory
from harbor.models.trial.config import EnvironmentConfig

config = EnvironmentConfig(import_path="my_package.environments:LocalEnv")
environment = EnvironmentFactory.create_environment_from_config(
    config,
    environment_dir=environment_dir,
    environment_name="task",
    session_id="trial__env",
    trial_paths=trial_paths,
    task_env_config=task_env_config,
)
```

`EnvironmentFactory.create_environment_from_import_path()` receives the same
paths/configuration and forwards resource overrides, persistent environment,
extra compose files, policy choices, and custom `kwargs`. If neither `type` nor
`import_path` is set, configuration fails. Built-in environment types use a
lazy registry and provider-specific extras; custom import paths bypass the
built-in enum but still must satisfy the base constructor and lifecycle.

Do not add a built-in enum value merely to make a third-party environment work.
Add a first-party registry entry only when the provider is shipped, documented,
versioned, and covered by preflight, capability, and mocked unit tests.

## Environment obligations

`BaseEnvironment` validates the task definition, resource enforcement mode,
GPU/TPU support, network policy, and Windows support during construction. A
provider must either enforce a requested policy or reject it. Override:

- `capabilities` with an `EnvironmentCapabilities` value for GPUs, TPUs,
  Windows, no-network, allowlists, dynamic policy, mounts, and compose.
- `resource_capabilities()` for job-level resource-policy preflight without
  constructing an environment.
- `preflight()` for credentials/config checks before trials are queued.
- `_validate_definition()` for required Dockerfile, image, Compose, or provider
  definition validation.

The required async methods are `start(force_build)`, `stop(delete)`,
`upload_file`, `upload_dir`, `download_file`, `download_dir`, and `exec`.
The live `exec` contract accepts `command`, optional `cwd`, `env`,
`timeout_sec`, and `user`, returning `ExecResult(stdout, stderr, return_code)`.
Provider code should preserve cancellation, return codes, and useful logs; it
must not silently weaken network or resource isolation.

A custom environment that returns `None` from `resource_capabilities()` skips
resource-policy preflight, which is appropriate only when the provider truly
cannot describe those policies. It is not evidence that requested CPUs,
memory, GPUs, or TPUs will be enforced.

## Plugins and extension tests

A plugin has two async hooks:

```python
from harbor.models.job.plugin import BaseJobPlugin

class AuditPlugin(BaseJobPlugin):
    async def on_job_start(self, job) -> None:
        # Register hooks or initialize local state.
        return None

    async def on_job_end(self, job_result) -> None:
        return None
```

`PluginConfig` contains `import_path` and a `kwargs` mapping. `attach_job_plugin`
resolves either a full import path or a short entry-point name, constructs the
class, checks the `JobPlugin` protocol, and calls `on_job_start`. Finalization
calls `on_job_end`; failures are logged and do not prevent subsequent plugin
finalization unless the plugin itself is used in a fail-fast integration.

Declare a package entry point under the exact group `harbor.plugins`, for
example `name = "package.module:PluginClass"`. Inspect installed registrations
with `harbor plugins list`. A full `module:ClassName` path works without an
entry point. Test both a successful hook and rejection of a non-plugin class;
mock requests, uploads, telemetry, and registry mutations.

## Model connections

Set `MODEL_CONNECTION = ModelConnectionSpec(...)` on an installed agent when
it needs standardized credential routing. The spec supports:

- `default_provider` to pin routing regardless of a model prefix.
- `api_key_envs` and `base_url_envs` for agent-native variable names.
- `passthrough=True` when provider-native key, endpoint, and extra variables
  must be forwarded under their canonical or selected names.

`BaseAgent.model_connection` returns a `ResolvedModelConnection`. Resolution
uses explicit `extra_env` before ambient `os.environ`; it derives a provider
from `provider/model` or LiteLLM when possible, applies provider aliases, and
only supplies a provider default endpoint when a credential is resolved. Never
serialize or log the `api_key`; inspect only provider, configured endpoint, and
redacted environment names in tests. A custom gateway should use explicit key
and base URL names and test precedence, empty-key behavior, and no accidental
credential leakage.
