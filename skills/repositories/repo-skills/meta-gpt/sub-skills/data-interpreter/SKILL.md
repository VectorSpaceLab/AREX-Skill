---
name: data-interpreter
description: "Use MetaGPT Data Interpreter and RoleZero workflows for data
  analysis, notebook execution, DI benchmark prompts, and dynamic analyst/SWE
  roles."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data Interpreter

Use this sub-skill when the user asks to run or reason about MetaGPT Data Interpreter (DI), RoleZero, DataAnalyst, SWEAgent, Engineer2, or TeamLeader workflows for data analysis, planning, generated code execution, benchmark prompts, browser/tool-assisted analysis, or DI role debugging.

## Route Here When

- The request mentions `DataInterpreter`, `RoleZero`, `DataAnalyst`, `SWEAgent`, `Engineer2`, `TeamLeader`, DI benchmark tasks, open-ended DI tasks, or notebook-style code execution.
- The user wants an Iris/Titanic/Wine/House Prices-style analysis prompt, a DI benchmark task, an open-ended OCR/browser/email/image/game task prompt, or a `data_dir` layout check.
- The agent must diagnose DI planning, reflection, tool recommendation, generated-code execution, notebook timeout, or role/tool-command behavior without running an expensive LLM workflow.
- The user asks how DI uses tools such as browser, editor, terminal, custom registered tools, or `tools=["<all>"]` from a workflow perspective.

## Route Elsewhere

- Core MetaGPT CLI, startup commands, project generation, and software-company workflows belong in `software-company`.
- Tool registry internals, RAG/search/browser/editor implementation details, and data preprocessing tool internals belong in `rag-and-tools`.
- AFlow, SPO, optimizer, or experiment-environment workflows belong in `extensions-and-environments`.
- Serialization, storage, provenance stores, memory backends, or package-maintainer APIs belong in `maintainer-apis`.
- API-key/provider setup and cross-cutting package configuration errors should use the root MetaGPT troubleshooting guidance, then return here for DI-specific checks.

## First Moves

1. Confirm the user understands DI runs LLM calls and generated Python/tool code; do not treat DI examples or benchmark runners as safe smoke tests.
2. For import or constructor issues, run the bundled diagnostic helper: `python scripts/di_import_check.py`. Use `--strict` only when a nonzero exit should fail CI.
3. For dataset tasks, validate `data_dir`, `task_name`, and file placeholders with `references/data-formats.md` before constructing the prompt.
4. For code execution failures, inspect `references/workflows.md` and `references/troubleshooting.md` before re-running generated code.
5. For browser, editor, search, terminal, OCR, Stable Diffusion, email, or game-tool tasks, verify prerequisites and safety boundaries first; route implementation details to `rag-and-tools`.

## Bundled References

- `references/workflows.md`: DI quick starts, benchmark/open-ended task adaptation, planning/execution loops, notebook caveats, RoleZero/team workflows, and safe adaptation rules.
- `references/api-reference.md`: key DI roles, actions, constructor knobs, run patterns, tool recommenders, and safe diagnostic guidance.
- `references/data-formats.md`: DI dataset layout, `task_name` keys, `data_dir` behavior, prompt path placeholders, DABench notes, and test-fixture expectations.
- `references/troubleshooting.md`: API keys, missing datasets, credentials, browser/OCR/SD optional dependencies, notebook errors, long runs, and unsafe file execution.

## Runtime Safety

DI can write and execute Python, operate browser/editor/terminal tools, access networks, and process user data. Prefer sandboxed workspaces, inspect generated code before execution, protect credentials, and skip tasks requiring external API keys, downloads, browsers, Android/devices, Stable Diffusion services, OCR engines, or long LLM benchmarks unless the user explicitly provides those prerequisites.

Evidence provenance distilled from `examples/di/README.md`, DI example runners, `metagpt/roles/di/*`, `metagpt/actions/di/*`, tool library usage, and DI tests. These paths are provenance only; this sub-skill is intended to be self-contained at runtime.
