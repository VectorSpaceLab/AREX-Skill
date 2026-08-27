---
name: sandbox-and-security
description: "Guides PandasAI sandboxed code execution, the abstract Sandbox
  contract, Docker sandbox setup, and security troubleshooting for generated
  code."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Sandbox and Security

Use this sub-skill when a task asks how to isolate PandasAI-generated code,
whether to use the Docker sandbox, or how the abstract `Sandbox` contract
behaves.

PandasAI executes LLM-generated Python locally by default. If the app is public,
untrusted, or handling sensitive data, the user should consider a sandbox before
running generated code.

## Fast route

1. If the user needs only a conceptual decision, explain that sandboxing is
   optional but recommended for untrusted prompts or production exposure.
2. If the user needs a concrete runtime, prefer the Docker sandbox extension
   when Docker is available.
3. If Docker is unavailable or the user needs a custom runtime, implement a
   subclass of the abstract `Sandbox` interface and verify it with the bundled
   smoke script.
4. Once sandbox choice is settled, return to the conversational-analysis
   sub-skill for the chat workflow itself.

## Read next

- [`references/sandbox-workflows.md`](references/sandbox-workflows.md) for
  `Sandbox` contract details, Docker lifecycle, and execution patterns.
- [`references/security-model.md`](references/security-model.md) for security
  posture, code-execution expectations, and SQL-safety notes.
- [`references/troubleshooting.md`](references/troubleshooting.md) for missing
  Docker, missing package, subclass, or code-execution problems.
- [`scripts/sandbox_contract_smoke.py`](scripts/sandbox_contract_smoke.py) for a
  no-Docker contract smoke.

## Boundaries

- Route chat/response generation to
  [`../conversational-analysis/SKILL.md`](../conversational-analysis/SKILL.md).
- Route CLI login and dataset creation to
  [`../cli-and-project-ops/SKILL.md`](../cli-and-project-ops/SKILL.md).
- Do not assume Docker or the `pandasai-docker` package is present unless the
  user explicitly asks for the Docker sandbox.

## Safe validation

```bash
python sub-skills/sandbox-and-security/scripts/sandbox_contract_smoke.py
```

The helper uses a tiny in-memory subclass of `Sandbox`. It checks `start`,
`stop`, `execute`, SQL query extraction, and syntax compilation without Docker.

## Common gotchas

- `Sandbox.start`, `stop`, `_exec_code`, and `transfer_file` are abstract on the
  base class.
- `execute` auto-starts a sandbox the first time it is called.
- Generated code can still be unsafe if it runs outside a sandbox.
- SQL queries extracted from code are heuristics; dynamic query construction may
  not be fully visible to the extractor.
- The package's SQL sanitizer and code validator are separate protections; do
  not assume one replaces the other.
