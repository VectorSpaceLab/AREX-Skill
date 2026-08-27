---
name: setup-and-basics
description: "Install, verify, and troubleshoot the basic NVIDIA NeMo Guardrails
  package, extras, imports, and CLI without live providers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# setup-and-basics

Use this sub-skill when the task is about installing NVIDIA NeMo Guardrails, selecting extras, proving that the package imports, checking the CLI entry point, or explaining optional dependency import errors without contacting a live model provider.

## Route here for

- `pip install nemoguardrails`, Python version support, resolver or `pip check` failures.
- Choosing extras such as `server`, `eval`, `tracing`, `chat-ui`, `sdd`, `jailbreak`, `multilingual`, `gcp`, or cautious `all` installs.
- Minimal package health checks: version, top-level imports, testing helpers, and `python -m nemoguardrails --help`.
- Optional dependency errors that mention missing modules or `pip install 'nemoguardrails[extra]'`.
- Broken `nemoguardrails` console command where module invocation might still work.

## Route away

- Config folders, `config.yml`, Colang, rails selection, prompts, custom actions, or provider definitions: use `../configure-rails/SKILL.md`.
- `Guardrails`/`LLMRails` generation, server startup, LangChain/RunnableRails execution, streaming, `/v1/*` API usage: use `../run-rails/SKILL.md`.
- Evaluation, tracing, telemetry, metrics, or compliance reports: use `../evaluate-and-observe/SKILL.md`.
- Editing the source checkout, running maintainer tests, PR policy, or contribution workflow: use `../repo-development/SKILL.md`.

## Operating workflow

1. Confirm Python is `>=3.10,<3.14`; install with the smallest extra set that matches the requested feature. See `references/installation-and-extras.md`.
2. Run no-provider verification before attempting live chat, server, eval, or provider-specific workflows:
   - `python -m pip check`
   - `python -m nemoguardrails --help`
   - bundled `scripts/check_install.py`
3. Use `references/package-surface.md` to identify stable public imports and testing helpers.
4. Use `references/troubleshooting.md` for optional dependency, console-script, Python-version, moved-import, and FastEmbed/network-smoke pitfalls.

## Safe helper

Run the bundled helper from any working directory:

```bash
python sub-skills/setup-and-basics/scripts/check_install.py
python sub-skills/setup-and-basics/scripts/check_install.py --json
python sub-skills/setup-and-basics/scripts/check_install.py --check-cli
python sub-skills/setup-and-basics/scripts/check_install.py --check-module fastapi:server --check-module streamlit:eval
```

The helper imports package metadata and modules only. `--check-cli` checks CLI module importability without running a command. The helper does not instantiate rails, start servers, call providers, download models, or write files.
