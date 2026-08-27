---
name: cli-and-operations
description: "Operate the DeepXiv command-line interface safely: choose commands
  and flags, preserve output streams, manage tokens and local configuration, and
  recover from CLI errors."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DeepXiv CLI and operations

Use this route when the task is about invoking `deepxiv`, selecting CLI flags,
redirecting output, configuring credentials, or diagnosing a CLI failure. Keep
shell commands and token/configuration handling here; use the linked routes for
API-level research and local-agent behavior.

## Operating route

1. Establish that the executable is the DeepXiv 1.0 CLI and inspect
   `deepxiv --help` / `deepxiv --version` before relying on a flag. The expected
   source command set and options are in [the CLI reference](references/cli-reference.md).
2. Select the smallest command for the task. Use `ask` for a cited answer,
   `search` for candidate papers, `paper`/`pmc`/`biorxiv`/`medrxiv` for direct
   retrieval, and `trending` for a social-signal list.
3. Choose the backend-specific flags before running `ask`: arXiv uses
   `--top-k`; web uses `--search-type`, `--gl`, and `--hl`. Do not mix these
   partitions. See [the reference](references/cli-reference.md#ask).
4. For an answer that will be piped or saved, preserve the stream contract:
   answer text is stdout; citations, source annotations, quota notices, and
   progress are stderr. Use `--json` only when a complete structured payload is
   wanted.
5. Before an authenticated call, resolve credentials using
   [configuration guidance](references/configuration.md). Never put a real
   token or LLM key in a transcript, committed file, shell history, process
   listing, or generated report.
6. On failure, classify the message using
   [troubleshooting](references/troubleshooting.md) before retrying. In
   particular, a `403` from `ask` means the key lacks registered agentic access;
   it is not fixed by repeatedly retrying an auto-registered SDK token.

## Command boundary

This skill covers the hosted CLI surface, including `agent query` and
`agent config` only as invocation/configuration boundaries. Detailed `Reader`
methods, research sequencing, answer-source interpretation, and hosted-agent
API behavior belong to [reader-and-paper-research](../reader-and-paper-research/SKILL.md).
The local LangGraph/OpenAI-compatible agent's internals, budgets, tools, and
provider troubleshooting belong to [optional-local-agent](../optional-local-agent/SKILL.md).

## Safe verification helper

Run [scripts/cli_smoke.py](scripts/cli_smoke.py) from any working directory to
check that the installed package imports and that the CLI group exposes the
expected help and version without making a network request, reading
credentials, or writing configuration. It is deliberately not a live command
test.
