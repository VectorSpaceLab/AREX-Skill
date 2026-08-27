# Headroom CLI route map

Use the narrowest route below rather than loading the entire repo skill for every command.

| Command family | Owning route | Read when |
| --- | --- | --- |
| `headroom proxy`, `wrap`, `unwrap` | `sub-skills/proxy-wrap/SKILL.md` | A provider or coding agent must route through Headroom. |
| `headroom deploy`, `install`, `init`, `update` | `sub-skills/ops/SKILL.md` | Headroom must be installed, persisted, updated, or configured durably. |
| `headroom doctor`, `dashboard`, `inspect`, `perf`, `savings`, `output-savings`, `agent-savings` | `sub-skills/ops/SKILL.md` | The user needs health, savings, output shaping, or log analysis. |
| `headroom tools`, `sg`, `diff`, `loc` | `sub-skills/ops/SKILL.md` | The user wants bundled repo-navigation tools or their cache status. |
| `headroom evals` | `sub-skills/ops/SKILL.md` | The user wants memory/compression robustness/retention evals. |
| `headroom memory` | `sub-skills/memory/SKILL.md` | The task inspects or mutates a memory DB. |
| `headroom mcp` | `sub-skills/memory/SKILL.md` | The task installs, checks, or serves Headroom MCP. |
| `headroom learn`, `recover`, `audit-reads` | `sub-skills/memory/SKILL.md` for learn/recover; `ops` for audit reporting | The task mines failures, learns verbosity, or recovers wrapped state. |
| Python `compress`, `HeadroomClient`, `SharedContext` | `sub-skills/sdk/SKILL.md` | The user is integrating in Python. |
| TypeScript `compress`, `HeadroomClient`, `SharedContext` | `sub-skills/sdk/SKILL.md` | The user is integrating in Node/TypeScript. |

## Read-only first

Before any state-changing command, prefer:

```bash
headroom --help
headroom doctor --json
headroom install status --profile default
headroom tools doctor --json
```

Do not confuse `headroom mcp status` with proxy health: MCP registration and proxy reachability are separate checks.
