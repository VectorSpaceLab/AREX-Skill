---
name: agent-tools-and-providers
description: "Configure providers and safely operate leader-worker dispatch, text tool calls, repository tools, and literature search."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Agent tools and providers

Use this skill when a research project needs to configure the LLM endpoint or
when a worker must inspect files, search code, query literature, or hand an
experiment launch to monitoring. This skill describes the observable
dispatcher and tool-registry contracts; it does not run an experiment, install
source skills, or choose an execution backend.

## Quick routing

1. Confirm the provider, model, endpoint override, and credential *environment
   variable names*. Never put a secret value in a config file, prompt, report,
   or tool result.
2. Use `AgentDispatcher` for leader/worker calls and `ToolRegistry` for the
   worker's allow-listed tools. A worker has no direct filesystem, shell, or
   network access; it must emit the text protocol described in
   `references/text-tool-protocol.md`.
3. Select a worker by responsibility: `idea` for literature, `code` for
   implementation and launch, and `writing` for reports. Keep the tool set
   minimal and do not grant tools by copying another worker's list.
4. Treat the registry's returned JSON, especially `launch_experiment`'s `pid`
   and `log_file`, as authoritative. Do not replace them with numbers or paths
   guessed from model prose.
5. Before any write or command, use workspace-relative paths and the exact
   tool schemas in `references/tool-catalog.md`. Route long-running lifecycle
   and backend transport questions to the corresponding lifecycle/backend
   skills.

## Provider choices

`AgentDispatcher` supports `anthropic`, `openai`, `claude_cli`, and `codex_cli`.
The domestic aliases `deepseek`, `dashscope`, `qwen`, `moonshot`, `kimi`,
`zhipu`, and `glm` select an OpenAI-compatible endpoint while retaining the
original alias as `provider_label`. Presets, exact constructor behavior,
credential precedence, and model mapping are in
`references/provider-config.md`.

Prefer `anthropic` or `openai` for API calls and `claude_cli` when a pure text
CLI oracle is desired. `codex_cli` is suitable for leader/free-text work, but
is unsafe for authoritative worker handoff: its CLI runs its own built-in
agentic tools and cannot be forced into the registry protocol. The dispatcher
logs a warning whenever a codex worker receives tools; use another provider
for workers that write files or launch experiments.

## Dispatch contract

- `dispatch_leader(task, context)` keeps leader history within a cycle and
  parses a JSON decision. Leader history must be reset between cycles by the
  caller; the leader is not a worker tool loop.
- `dispatch_worker(agent_type, task, tool_registry)` starts a fresh worker
  conversation, appends the rendered schemas, executes parsed calls in order,
  and repeats until a response has no calls or the worker's hard `max_turns`
  limit is reached.
- Tool results are returned to the model in a new user message. A non-dict
  `args` value is converted into a structured error and is never expanded as
  keyword arguments. Unknown tools also return a structured error.
- For a code worker, a successful `launch_experiment` result is surfaced as
  `experiment_launched`, `pid`, and (when supplied) `log_file`. This result is
  the handoff consumed by monitoring.

## Safe operating rules

- A tool call is real only when it is a top-level `<tool_call>` block. Calls
  inside a triple-backtick fenced block are illustrative and are suppressed.
- Normalize paths before touching the backend. Absolute paths, empty paths,
  `..` components, and symlink escapes are rejected. Writes additionally
  protect the basenames `state.json`, `MEMORY_LOG.md`, `PROJECT_BRIEF.md`, and
  `.lock`; protected files may still be read when otherwise valid.
- `run_shell` and `launch_experiment` parse with `shlex.split` and invoke the
  backend without a shell. Empty commands, malformed quoting, and a blocked
  executable (`rm`, `sudo`, `su`, `mkfs`, `dd`, `shutdown`, `reboot`,
  `poweroff`, or `halt`) fail before execution. Do not treat this as a complete
  privilege sandbox: explicitly invoking a shell interpreter remains a
  separate capability and should be avoided.
- Repository searches are read-only, skip VCS/cache directories, skip
  symlinks and oversized/binary files, and return bounded results. Literature
  calls have network side effects and must be made only when the user permits
  them; failure is reported as JSON rather than retried blindly.

## Verification

Run the bundled `scripts/validate_provider_config.py` with representative
provider/model/override combinations. It performs no network request, does
not read credential values, and prints only normalized non-secret metadata.
For parser/security review, use synthetic fenced-call, traversal, and
semicolon-payload cases and verify that no file is created and no backend call
is made before accepting a worker handoff.

## Further reference

- `references/provider-config.md`: constructor fields, aliases, SDK/CLI paths,
  precedence, and failure behavior.
- `references/tool-catalog.md`: worker allow-lists, exact schemas, result
  shapes, bounds, protection, and literature behavior.
- `references/text-tool-protocol.md`: parsing, multi-turn result handoff,
  fenced-call suppression, and authoritative PID handling.
- `references/troubleshooting.md`: predictable configuration, parser, path,
  shell, network, and CLI failure responses.

Do not use this skill to launch training or to poll a PID. For those tasks route
to experiment lifecycle and execution/monitoring skills, respectively. For
source-skill installation or export route to skills-and-installation.
