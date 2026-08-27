# MCP, skills, ACP, and simulated-user bridges

These surfaces transport capabilities into an agent trial. They do not turn a
missing server, skill, model, or provider credential into a successful run.
Keep task authoring, run execution, and implementation boundaries distinct.

## MCP configuration

The validated data model is `MCPServerConfig`:

```toml
[[environment.mcp_servers]]
name = "service"
transport = "streamable-http" # sse | streamable-http | stdio
url = "http://service:8000/mcp"
# For stdio instead:
# transport = "stdio"
# command = "python"
# args = ["server.py"]
```

`sse` and `streamable-http` require `url`; `stdio` requires `command` and may
have `args`. The legacy transport spelling `http` normalizes to
`streamable-http`. The task can declare servers under
`[environment].mcp_servers`; runtime `--mcp-config FILE` adds servers to the
job/trial agent. JSON, YAML, and TOML loaders accept `mcpServers` or
`mcp_servers`; Claude-shaped mapping entries gain their name from the key,
`type` is accepted as a transport alias, and unsupported fields are dropped
with debug logging. Validate the resulting Pydantic model before starting a
container.

At trial initialization, task servers are merged with runtime agent servers
by `name`; later runtime entries replace earlier task entries. The effective
list is passed to the agent constructor as `mcp_servers`. The agent adapter
then translates the model into its native configuration, which differs across
agents. A valid Harbor config does not prove the remote URL is reachable or the
stdio command is installed. Use a local fake server/command or mocked adapter
configuration tests first.

A task-side Docker Compose MCP server belongs to benchmark authoring. A custom
MCP adapter, automatic registration logic, or framework-side bridge belongs to
this skill. Compose and cloud compatibility are provider capabilities; local
Docker is the conservative choice for multi-container task-side MCP tests.

## Injected skills

A skill is a directory containing `SKILL.md`. Agent configuration accepts
repeatable local paths, git repository shorthand, or full repository/subtree
sources. Harbor resolves non-local sources to cached local directories before
trial execution, computes provenance/digests in the job lock, and uploads the
resolved skill tree into the environment.

Runtime `--skill`/`--skills` values are appended to each configured job agent;
for a standalone trial they are appended to its agent. If multiple skills have
the same directory name, the later source wins. Keep source order explicit when
an override is intentional. The task's `environment.skills_dir` controls the
remote destination; it must be absolute when injected skills are present. If
omitted, Harbor uses its default remote skills directory. A task-declared skill
source and runtime injected skill are separate provenance inputs; do not assume
one is overwritten merely because the destination is shared.

The agent adapter owns native discovery. Some installed agents copy skill
contents into their native config directory; SDK agents receive skill paths;
others may not support skills. Test that the selected adapter sees a minimal
fixture with one `SKILL.md`, not only that the source path exists. Avoid putting
secrets, source-checkout paths, or answer-bearing benchmark files in skills.

## ACP registry agents

The built-in `acp` agent runs an Agent Client Protocol implementation from an
ACP registry record. The declarative shorthand is `acp:<agent-id>` or
`acp:<agent-id>@<version>` wherever an agent is accepted. An omitted version
requires registry resolution during setup; config creation itself is intended
not to perform network I/O. An explicit registry entry path or a pinned source
can be supplied through ACP kwargs when the generic runner is the desired
adapter.

Important ACP options include `auth_policy` (`auto`, `explicit`, or
`disabled`), `permission_mode` (`allow` or `deny`), distribution preference
among binary/npx/uvx, a registry ref/cache directory, and the requested model.
ACP setup may install Node/ACPX and fetch a registry record or source; this is
an execution and network gate. It writes ACP logs/events/summary and a
trajectory document, but those artifacts do not prove the target's model
credential worked. Test registry parsing, invalid distribution combinations,
permission validation, and runner environment construction without fetching.

## Bridges and simulated users

A simulated-user trial has a target agent and a user agent in one environment.
The target starts without the private task instruction; the user agent receives
the task and communicates through a configured bridge. The live models are:

```python
from harbor.models.trial.config import UserAgentConfig
from harbor.models.bridge import BridgeConfig, BridgeKind

user = UserAgentConfig(
    name="user-agent",
    model_name="provider/model",
    bridge=BridgeConfig(kind=BridgeKind.ACP),
)
```

`BridgeKind` currently contains `acp`. `BaseBridge` requires `setup`,
`prompt`, `env`, `export_trajectory`, and `teardown`; a bridge can also expose
input files and enrich the user context. Register a new kind with
`register_bridge()` only when the implementation is shipped and its config,
trajectory, teardown, and secret handling are tested.

The ACP bridge requires the target agent to advertise `BridgeKind.ACP` in
`SUPPORTED_BRIDGES` and to implement `ACPAgentMixin` methods that provide the
ACP command, environment, installation, and teardown behavior. The bridge
installs a pinned ACPX client, creates a session config, starts a session,
exports a bridge trajectory, and tears it down. It rejects reserved override
keys and unsupported target agents before execution. A plain custom
`BaseAgent` is not automatically bridge-compatible.

The user prompt is composed in this order: persona, bridge instructions, then
private task instruction. The default template uses `{{ persona }}`,
`{{ bridge_instructions }}`, and `{{ instruction }}`. A custom Jinja template
must include the latter two, may include only those three variables, and must
include `{{ persona }}` if a persona file is supplied. Unknown variables,
syntax errors, and an ignored persona are validation errors.

Both roles share one environment and installation prefix. If the user and
target are the same named agent, conflicting version pins are rejected because
one install would silently win. Built-in target bridge support is checked at
job preflight; import-path and ACP registry targets are checked at trial setup.
Bridge credentials and model keys are separate from the target's task-side
MCP credentials. Never expose the private task instruction in target logs,
bridge config, or a skill intended only for the target.

## Extension checklist

For a new MCP/skill/bridge integration, verify in this order:

1. Pydantic config rejects incomplete transport or bridge fields.
2. Factory/trial wiring passes the effective servers, skills directory, and
   bridge env to the intended role only.
3. A fake environment records setup, command, upload, export, and teardown
   calls in the expected order.
4. A minimal local fixture proves merge precedence, skill collision policy,
   prompt-template validation, and trajectory output naming.
5. Any network, registry fetch, model call, provider SDK, or ACPX installation
   is separately gated and mocked in default tests.
