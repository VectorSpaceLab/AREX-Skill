# Project Scaffolding Detailed Guide

This reference preserves the detailed first-party guidance for the `scaffold` sub-skill. Read `scaffold/SKILL.md` first for routing and use this file for deep workflow details.

# ADK Project Scaffolding Guide

> **Requires:** `agents-cli` (`uv tool install google-agents-cli`) — [install uv](https://docs.astral.sh/uv/getting-started/installation/index.md) first if needed.

Use the `agents-cli` CLI to create new ADK agent projects or enhance existing ones with deployment, CI/CD, and infrastructure scaffolding.

---

## Prerequisite: Clarify Requirements (MANDATORY for new projects)

**Before scaffolding a new project, load `../../workflow/SKILL.md` and complete Phase 0** — clarify the user's requirements before running any `scaffold create` command. Ask what the agent should do, what tools/APIs it needs, and whether they want a prototype or full deployment.

---

## Step 1: Choose Architecture

**Mapping user choices to CLI flags:**

| Choice | CLI flag |
|--------|----------|
| Retrieval/RAG, sandboxed execution, cross-session memory, OAuth consent, guardrails, scheduled runs | **No flag** — these come from clone-and-study recipes; see the topic index in `../../adk-code/SKILL.md` → `samples.md` |
| A2A protocol | built into every ADK agent — scaffold normally (`--agent adk`) |
| Prototype (no deployment) | `--prototype` |
| Deployment target | `--deployment-target <agent_runtime\|cloud_run\|gke>` |
| CI/CD runner | `--cicd-runner <github_actions\|google_cloud_build>` |
| Session storage | `--session-type <in_memory\|cloud_sql\|agent_platform_sessions>` |

### Product name mapping

Older names → CLI values (`vertexai` SDK package name unchanged):

- Agent Engine / Vertex AI Agent Engine → `--deployment-target agent_runtime`
- Agent Engine sessions / Agent Platform Sessions → `--session-type agent_platform_sessions`
- Vertex AI Search / Vertex AI Vector Search / RAG → clone-and-study recipe, not a flag

> **Removed flags.** `--datastore`, the `agentic_rag` template, and `agents-cli infra datastore` /
> `agents-cli data-ingestion` no longer exist. If you reach for one, you want a recipe instead.

---

## Step 2: Create or Enhance the Project

### Create a New Project

```bash
agents-cli scaffold create <project-name> \
  --agent <template> \
  --deployment-target <target> \
  --region <region> \
  --prototype
```

**Constraints:**
- Project name must be **26 characters or less**, lowercase letters, numbers, and hyphens only.
- Do NOT `mkdir` the project directory before running `create` — the CLI creates it automatically. If you mkdir first, `create` will fail or behave unexpectedly.
- Auto-detect the guidance filename based on the IDE you are running in and pass `--agent-guidance-filename` accordingly (`GEMINI.md` for Antigravity CLI, `CLAUDE.md` for Claude Code, `AGENTS.md` for OpenAI Codex/other).
- When enhancing an existing project, check where the agent code lives. If it's not in `app/`, pass `--agent-directory <dir>` (e.g. `--agent-directory agent`). Getting this wrong causes enhance to miss or misplace files.

### Reference Files

| File | Contents |
|------|----------|
| `flags.md` | Full flag reference for `create` and `enhance` commands |

### Enhance an Existing Project

```bash
agents-cli scaffold enhance . --deployment-target <target>
agents-cli scaffold enhance . --cicd-runner <runner>
```

Run this from inside the project directory (or pass the path instead of `.`).

### Upgrade a Project

Upgrade an existing project to a newer agents-cli version, intelligently applying updates while preserving your customizations:

```bash
agents-cli scaffold upgrade                # Upgrade current directory
agents-cli scaffold upgrade <project-path> # Upgrade specific project
agents-cli scaffold upgrade --dry-run      # Preview changes without applying
agents-cli scaffold upgrade --auto-approve  # Auto-apply non-conflicting changes
```

### Execution Modes

The CLI defaults to **strict programmatic mode** — all required params must be supplied as CLI flags or a `UsageError` is raised. No approval flags needed. Pass all required params explicitly.

### Common Workflows

**Always ask the user before running these commands.** Present the options (CI/CD runner, deployment target, etc.) and confirm before executing.

```bash
# Add deployment to an existing prototype (strict programmatic)
agents-cli scaffold enhance . --deployment-target agent_runtime

# Add CI/CD pipeline (ask: GitHub Actions or Cloud Build?)
agents-cli scaffold enhance . --cicd-runner github_actions
```

---

## Template Options

| Template | Deployment | Description |
|----------|------------|-------------|
| `adk` | Agent Runtime, Cloud Run, GKE | Standard ADK agent (default); A2A protocol built in |

> **`adk` is the only template.** Capabilities beyond it — retrieval, sandboxed execution, memory,
> OAuth, guardrails — are clone-and-study recipes, not templates. See the topic index in
> `../../adk-code/SKILL.md` → `samples.md`.

---

## Deployment Options

| Target | Description |
|--------|-------------|
| `agent_runtime` | Managed by Google (Vertex AI Agent Runtime). Container-based — Agent Engine builds the project Dockerfile. Sessions handled automatically. |
| `cloud_run` | Container-based deployment. More control; you build and deploy the Dockerfile. |
| `gke` | Container-based on GKE Autopilot. Full Kubernetes control. |
| `none` | No deployment scaffolding. Code only (still includes a Dockerfile). |

### "Prototype First" Pattern (Recommended)

Start with `--prototype` to skip CI/CD and Terraform. Focus on getting the agent working first, then add deployment later with `scaffold enhance`:

```bash
# Step 1: Create a prototype
agents-cli scaffold create my-agent --agent adk --prototype

# Step 2: Iterate on the agent code...

# Step 3: Add deployment when ready
agents-cli scaffold enhance . --deployment-target agent_runtime
```

### Agent Runtime and session_type

When using `agent_runtime` as the deployment target, Agent Runtime manages sessions internally. If your code sets a `session_type`, clear it — Agent Runtime overrides it.

---

## Step 3: Load Dev Workflow

After scaffolding, immediately load `../../workflow/SKILL.md` — it contains the development workflow, coding guidelines, and operational rules you must follow when implementing the agent.

**Key files to customize:** `app/agent.py` (instruction, tools, model), `app/tools.py` (custom tool functions), `.env` (project ID, location, API keys).
**Files to preserve:** `agents-cli-manifest.yaml` (CLI reads this), deployment configs under `deployment/`, `Makefile`, `app/__init__.py` (the `App(name=...)` must match the directory name — default `app`), and the generated runtime/A2A infra (`app/fast_api_app.py`, `app/app_utils/a2a.py`, `app/app_utils/services.py`, `Dockerfile`) — these wire up serving, sessions, and the built-in A2A surface; don't hand-edit them.

**Adapting a recipe:** copy its `app/`, `infra/terraform/`, and any ingestion or provisioning into
your scaffolded project, then run provisioning from the recipe's own `Makefile` (e.g.
`make setup-infra`). Start from its `AGENTS.md`.

**Verifying your agent works:** Use `agents-cli run "test prompt"` for quick smoke tests, then `agents-cli eval generate` and `agents-cli eval grade` for systematic validation. Do NOT write pytest tests that assert on LLM response content — that belongs in eval.

---

## Scaffold as Reference

When you need specific files (Terraform, CI/CD workflows, Dockerfile) but don't want to scaffold the current project directly, create a temporary reference project in `/tmp/`:

```bash
agents-cli scaffold create /tmp/ref-project \
  --agent adk \
  --deployment-target cloud_run
```

Inspect the generated files, adapt what you need, and copy into the actual project. Delete the reference project when done.

This is useful for:
- Non-standard project structures that `enhance` can't handle
- Cherry-picking specific infrastructure files
- Understanding what the CLI generates before committing to it

---

## Critical Rules

- **NEVER skip requirements clarification** — load `../../workflow/SKILL.md` Phase 0 and clarify the user's intent before running `scaffold create`
- **NEVER change the model** in existing code unless explicitly asked
- **NEVER `mkdir` before `create`** — the CLI creates the directory; pre-creating it causes enhance mode instead of create mode
- **NEVER create a Git repo or push to remote without asking** — confirm repo name, public vs private, and whether the user wants it created at all
- **Always ask before choosing CI/CD runner** — present GitHub Actions and Cloud Build as options, don't default silently
- **Agent Runtime clears session_type** — if deploying to `agent_runtime`, remove any `session_type` setting from your code
- **Start with `--prototype`** for quick iteration — add deployment later with `enhance`
- **Project names** must be ≤26 characters, lowercase, letters/numbers/hyphens only
- **NEVER write A2A code from scratch** — A2A is built into every Python ADK agent (`adk`); the A2A Python API surface (import paths, `AgentCard` schema, `to_a2a()` signature) is non-trivial and changes across versions. Scaffold normally; never hand-write the A2A surface.

---

# Examples

Using scaffold as reference:
User says: "I need a Dockerfile for my non-standard project"
Actions:
1. Create temp project: `agents-cli scaffold create /tmp/ref --agent adk --deployment-target cloud_run`
2. Copy relevant files (Dockerfile, etc.) from /tmp/ref
3. Delete temp project
Result: Infrastructure files adapted to the actual project

---

A2A project:
User says: "Build me a Python agent that exposes A2A and deploys to Cloud Run"
Actions:
1. Follow the standard flow (understand requirements, choose architecture, scaffold)
2. `agents-cli scaffold create my-a2a-agent --agent adk --deployment-target cloud_run --prototype`
Result: Valid A2A imports and Dockerfile — no manual A2A code written.

---

## Troubleshooting

### `agents-cli` command not found

See `../../workflow/SKILL.md` → **Setup** section.

---

## Related Skills

- `../../workflow/SKILL.md` — Development workflow, coding guidelines, and the build-evaluate-deploy lifecycle
- `../../adk-code/SKILL.md` — ADK Python API quick reference for writing agent code
- `../../deploy/SKILL.md` — Deployment targets, CI/CD pipelines, and production workflows
- `../../eval/SKILL.md` — Evaluation methodology, dataset schema, and the eval-fix loop
