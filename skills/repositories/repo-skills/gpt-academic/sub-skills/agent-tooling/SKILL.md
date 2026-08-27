---
name: agent-tooling
description: "Operate GPT Academic Void Terminal, Code Interpreter, Commandline
  Assistant, and natural-language plugin dispatch workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Agent Tooling

Use this sub-skill when the user wants GPT Academic to choose tools, run generated Python, interpret uploaded files, modify configuration, or execute/suggest shell commands through agent-like plugins.

## Trigger phrases

Read this sub-skill for “虚空终端”, “Void Terminal”, “CodeInterpreter”, “动态代码解释器”, “Commandline Assistant”, “use natural language to call a plugin”, “modify GPT Academic config”, “run a command”, “generate code to process this file”, or “dynamic function generation”.

## First decisions

1. Classify the request as direct plugin use, Void Terminal, Code Interpreter, Commandline Assistant, or too risky without confirmation.
2. Run the request classifier for a first-pass safety route:

```bash
python sub-skills/agent-tooling/scripts/classify_agent_request.py "<user request>"
```

3. Ask before any action that mutates files/config, runs shell commands, deletes data, calls external services, or executes generated code.
4. If a deterministic domain plugin exists, prefer the owning sub-skill over a generic agentic route.

## Route map

| User goal | Surface | Read next |
| --- | --- | --- |
| ask GPT Academic to choose a plugin | Void Terminal / natural-language dispatch | `references/workflows.md` |
| run generated Python on an uploaded file | Code Interpreter | `references/workflows.md`, `references/safety.md` |
| ask for shell command help | Commandline Assistant | `references/safety.md` |
| modify app config by instruction | Void Terminal, but only with explicit confirmation | `references/safety.md`, root `references/configuration.md` |
| deterministic PDF/code/media workflow | owning plugin/sub-skill | sibling sub-skill first |

## Boundaries

- Use `../academic-docs/SKILL.md`, `../programming-code/SKILL.md`, or `../multimodal-media/SKILL.md` first when the user already knows the domain workflow.
- Use `../conversation/SKILL.md` for provider setup, search, RAG, and normal chat.
- Treat Code Interpreter and shell routes as execution workflows, not just conversation.
