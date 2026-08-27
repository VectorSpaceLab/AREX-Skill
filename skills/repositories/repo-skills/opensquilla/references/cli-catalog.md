# OpenSquilla CLI Catalog

Use `opensquilla <command> --help` as the final authority for the installed version.

| Command family | Main purpose | Gateway | Route |
| --- | --- | --- | --- |
| `onboard`, `gateway`, `doctor` | First run, lifecycle, and readiness | Lifecycle target | setup-and-gateway |
| `configure`, `providers`, `models`, `router`, `search`, `config` | Provider/model/router/search configuration and inspection | Mixed; status/query may be live | configuration-and-routing |
| `chat`, `agent`, `code-task` | Interactive or automated agent work | Chat normally; standalone/local modes exist | cli-and-automation |
| `sessions`, `memory`, `agents`, `cron`, `cost`, `diagnostics`, `reset` | Durable state and operations | Usually yes | cli-and-automation |
| `replay`, `bundle`, `dist`, `migrate`, `recovery`, `sandbox`, `init`, `uninstall` | Local inspection, migration, safety, and cleanup | Local/offline or process-owning | cli-and-automation |
| `channels` | Channel catalog, configuration, runtime, pairing, and certification | Runtime/status yes | channels-and-integrations |
| `mcp-server` | Stdio bridge from an MCP client to the gateway | Yes | channels-and-integrations |
| `skills` | Skill catalog, managed installs, taps, MetaSkill runs/proposals | Mixed; many inspections are local | skills-and-meta |

## Automation Defaults

Prefer `--json` when supported. Bound unattended work with explicit timeout, iteration, provider-retry, workspace, scratch, transcript, usage, and session database settings. Distinct parallel workers need distinct state roots and output paths. Do not suppress confirmation or destructive-operation warnings merely to make a command non-interactive.

## Mutation Checklist

Before a command changes state, identify its target and rollback path. In particular, review configuration writes, gateway restart/reload, channel edits, Skill catalog changes, MetaSkill proposal acceptance, cron mutation, migration `--apply`, session deletion/reset, and uninstall purge flags. Run migration and uninstall dry-run/preview paths first when available.
