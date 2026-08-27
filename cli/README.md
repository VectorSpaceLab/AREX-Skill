# DisCo

DisCo is a skill-powered research agent for the terminal. Its two explicit
roles separate reusable skill authoring from research and implementation work:

- **Creator** builds, imports, extends, and verifies skills.
- **Researcher** uses operating skills and dynamic workflows to complete tasks.

DisCo is published as `@auto-ml-skills/disco` and installs one executable,
`disco`. The package contains its own fork of Pi coding-agent v0.83.0; it does
not depend on `@earendil-works/pi-coding-agent`, and it does not discover
resources from `.pi` or `~/.pi`.

## Requirements

- Node.js 22.19.0 or newer
- Credentials for at least one supported model provider, or a configured local
  provider

## Install

```bash
npm install -g @auto-ml-skills/disco
disco
```

Use `/login` to configure a subscription or API-key provider. API keys can also
be supplied through provider environment variables such as
`ANTHROPIC_API_KEY` or `OPENAI_API_KEY`.

Update a global npm installation with:

```bash
disco update
```

Install and manage the published repository skill collection separately from
the CLI package:

```bash
disco repo-skills install
disco repo-skills status
disco repo-skills update
```

`status` is offline and checks the recorded commit, managed digests, router
state, and coverage of the live repository skill IDs. `update` performs the
remote check.

Updates preserve repo skills created or imported locally by Creator. Conflicting
changes to an official managed ID stop the update unless `--force` is supplied;
forced replacement writes a backup first. Git is required for install/update.

The repository router participates in automatic Researcher skill selection by
default. Disable or restore only that automatic entry point with:

```bash
disco repo-skills router disable
disco repo-skills router enable
```

Disabling the router does not remove it: explicit
`/skill:repo-skills-router` invocation remains available in a new Researcher
session.

`disco update` updates `@auto-ml-skills/disco`, not Pi. Use
`disco update --models`, `disco update --extensions`, or `disco update --all`
for the other documented update targets.

## Creator and Researcher

Researcher is the default for a new session:

```bash
disco --agent-mode researcher
disco --agent-mode researcher -p "Reproduce this paper's primary result"
```

Use Creator when the output is a reusable skill:

```bash
disco --agent-mode creator
disco --agent-mode creator -p "Inspect /path/to/repo and draft a skill creation plan"
```

In an interactive session, `/creator` and `/researcher` switch mode and rebuild
the mode-specific resource context. Sessions remember their mode when resumed.

Skills can declare `metadata.disco-role` in their frontmatter:

| Role | Loaded in Creator | Loaded in Researcher |
| --- | --- | --- |
| `meta` | yes | no |
| `operating` | no | yes |
| `shared` | yes | yes |

A skill without `disco-role` keeps the compatibility default, `operating`.
Invalid role values are rejected with a diagnostic.

## Skills and project resources

DisCo automatically discovers its own resources from:

- `~/.disco/agent/` for user settings, credentials, sessions, extensions,
  skills, prompts, and themes;
- `.disco/` for trusted project settings and resources;
- `~/.agents/skills/` and ancestor `.agents/skills/` for generic agent skills;
- `AGENTS.md` and `CLAUDE.md` context files in the normal ancestor chain.

Pi-specific `.pi`, `~/.pi`, `PI_CODING_AGENT_DIR`, and `PI_PACKAGE_DIR`
locations do not participate in DisCo discovery. Explicit paths supplied by the
user remain supported and still pass through project trust and skill-role
checks.

See [Skills](docs/skills.md), [Settings](docs/settings.md), and
[Security](docs/security.md) for the complete loading and trust rules.

## Dynamic workflows

The interactive runtime includes a workflow tool and commands for concurrent,
multi-phase research:

- `/deep-research <question>` performs web research with cross-checking.
- `/adversarial-review <task>` investigates findings and challenges them with
  independent reviewers.
- `/workflows` opens saved and active workflow controls.
- `/workflows-models` configures workflow model tiers.
- `/effort high|ultra|off` and `/ultracode` control standing workflow effort.

Workflow runs support structured results, model routing, bounded concurrency,
cancellation, saved workflows, persisted run state, and optional git
worktrees.

## CLI examples

```bash
# Interactive session
disco

# One-shot print mode
disco -p "Summarize this repository"

# Include files in the initial request
disco @README.md "Review this documentation"

# Continue or browse sessions
disco --continue
disco --resume

# JSONL or RPC integration
disco --mode json -p "Inspect the current project"
disco --mode rpc

# Package-managed resources
disco install npm:@example/disco-skills
disco list
```

Run `disco --help` for all CLI flags. The documentation index is at
[docs/index.md](docs/index.md).

## Extensions and packages

Extensions can add tools, commands, event handlers, providers, and terminal UI.
A DisCo package can bundle extensions, skills, prompts, and themes with a
`disco` manifest in `package.json`.

See [Extensions](docs/extensions.md), [DisCo packages](docs/packages.md), and
the bundled [examples](examples/README.md).

## Programmatic use

The same package exposes a low-level, headless SDK for Node.js applications:

```typescript
import { createAgentSession, SessionManager } from "@auto-ml-skills/disco";

const { session } = await createAgentSession({
  cwd: process.cwd(),
  sessionManager: SessionManager.inMemory(process.cwd()),
});

await session.prompt("Summarize this project");
```

Importing the SDK does not start the TUI, splash, version check, or self-update
lifecycle. The SDK uses DisCo defaults (`.disco` and `DISCO_*`) unless the
caller explicitly supplies paths or a custom resource loader. See
[SDK](docs/sdk.md) for lifecycle, model, tool, and extension examples.

## Documentation

- [Quickstart](docs/quickstart.md)
- [Usage and CLI](docs/usage.md)
- [Providers](docs/providers.md)
- [Models](docs/models.md)
- [Environment variables](docs/environment-variables.md)
- [Sessions](docs/sessions.md)
- [RPC](docs/rpc.md)
- [Development](docs/development.md)

## License and upstream

DisCo is licensed under the MIT License. Its internal coding-agent fork is
based on Pi v0.83.0 at commit
`845d6ff1f6643aba440341cce877ce1c43ebbc39`; attribution and third-party
notices are recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
