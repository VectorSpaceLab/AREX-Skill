---
name: ops
description: "Operate Headroom installs, durable deployments, diagnostics,
  savings reports, output shaping, evals, and bundled tools."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Headroom ops

Use this sub-skill when the user needs to install, update, deploy, diagnose, report on, or maintain a Headroom runtime without changing application code.

## Read this for

- `headroom deploy` and `headroom install ...` persistent proxy profiles.
- `headroom init ...` durable agent hooks/provider routing for supported agents.
- `headroom update` and install-method guidance.
- `headroom doctor`, `dashboard`, `inspect`, `perf`, `savings`, `output-savings`, `agent-savings`, `audit-reads`, and `capture network-diff`.
- `headroom tools ...` bundled `sg`, `diff`, and `loc` helpers.
- `headroom evals ...` commands and when not to run expensive or API-key-dependent evals.
- Cross-cutting filesystem roots and path overrides.

## Route elsewhere

- `headroom proxy`, provider base URLs, `headroom wrap`, and `headroom unwrap`: read `../proxy-wrap/SKILL.md`.
- `headroom memory`, `headroom mcp`, `headroom learn`, `headroom recover codex`, and CCR retrieval: read `../memory/SKILL.md`.
- Direct Python or TypeScript SDK usage: read `../sdk/SKILL.md`.

## First checks

1. Verify the package and CLI:

   ```bash
   python -c "import headroom; print(headroom.__version__)"
   headroom --version
   ```

2. For a broad diagnosis, run:

   ```bash
   headroom doctor
   python scripts/diagnose_headroom_install.py --check-cli
   ```

3. For durable deployment status, use:

   ```bash
   headroom install status --profile default
   ```

4. For token/cost reporting, prefer the least invasive read-only command first:

   ```bash
   headroom savings
   headroom perf --hours 24
   headroom output-savings
   ```

## References and helper

- `references/cli-reference.md` catalogs operator-facing commands, safe checks, and side-effect boundaries.
- `references/workflows.md` gives task-oriented install, deployment, diagnostics, reporting, tools, and eval recipes.
- `references/troubleshooting.md` maps common symptoms to recovery steps.
- `scripts/diagnose_headroom_install.py` is a safe local checker for imports, CLI availability, and canonical path roots.

## Safety rules

- Do not run `headroom update`, `headroom deploy`, `headroom install apply/remove`, `headroom init`, `headroom savings --reset`, `headroom memory purge`, or any command that mutates user config/state unless the user explicitly wants that side effect.
- Treat user configuration files such as Claude, Codex, OpenClaw, OpenCode, and shell startup files as user-owned; if a file is malformed, instruct the user to fix or move it rather than overwriting it.
- Do not paste API keys, bearer tokens, cloud profiles, proxy credentials, or private paths into examples.
- If a command depends on past proxy logs, savings ledgers, or a running proxy, first check whether the relevant file or endpoint exists and explain empty results as normal on a new install.
