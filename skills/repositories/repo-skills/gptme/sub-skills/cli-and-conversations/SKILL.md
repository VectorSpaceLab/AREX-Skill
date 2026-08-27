---
name: cli-and-conversations
description: "Operate gptme from the terminal: CLI prompts, conversation logs,
  slash commands, automation, and persistent agent commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# cli-and-conversations

Use this sub-skill when the task is about running `gptme` from a terminal, shaping prompts, managing chat histories, using slash commands, queuing follow-up prompts, building non-interactive automation, or understanding the `gptme-agent` management CLI.

Route away when the task is mainly about:

- provider credentials, default model choice, OAuth, or config precedence: use the configuration/providers sub-skill.
- built-in tool internals, custom tools, plugins, hooks, skills, lessons, MCP, browser, or computer-use setup: use the tools/extensibility sub-skill.
- `gptme-server`, REST/SSE, Web UI, ACP, TUI, deployment, or hosted access: use the server/protocols sub-skill.
- evaluation suites, SWE-bench/T-bench, Docker benchmark runs, or leaderboard processing: use the evals/benchmarks sub-skill.
- maintaining a `gptme` checkout, running the contributor test suite, releases, or Web UI development: use the repo-development sub-skill.

## Read first

- [references/cli-reference.md](references/cli-reference.md) for install/start patterns, main CLI options, prompt/context syntax, slash-command map, tool-selection syntax, and `gptme-agent` command families.
- [references/conversations-and-automation.md](references/conversations-and-automation.md) for named conversations, resume/search/fork, multiprompts, queued prompts, non-interactive automation, log layout, and persistent agent workflows.
- [references/troubleshooting.md](references/troubleshooting.md) for missing explicit local paths, resume/fork confusion, non-interactive pitfalls, tool allowlist errors, stdin behavior, context minimization, and agent service issues.

## Safe helpers

- [scripts/build_gptme_command.py](scripts/build_gptme_command.py) builds a shell-quoted `gptme` command from explicit prompt/model/tool/context/name flags without executing it.
- [scripts/inspect_conversation_log.py](scripts/inspect_conversation_log.py) summarizes and redacts a `conversation.jsonl` file, one conversation directory, or a directory of conversation directories without importing `gptme`.

## Fast operating checklist

1. Confirm the user wants terminal CLI/conversation behavior, not provider or tool internals.
2. Prefer named conversations for resumable work: `gptme --name <conversation> "task"`.
3. Use the standalone `-` argument only to separate chained turns; a lone `-` by itself is a literal prompt, not a stdin marker.
4. For tight startup context, combine `--system short`, a narrow `--tools` value, and either `--context files` or `--no-workspace`.
5. For automation, use `--non-interactive`; add `--output-format json` only with non-interactive mode.
6. If diagnosing logs, inspect an explicit log path with the bundled inspector before assuming which conversation `--resume` will choose.
