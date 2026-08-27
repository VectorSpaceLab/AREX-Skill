# Upsonic Package Overview

## Purpose

Upsonic is a Python framework for building production-oriented AI agents, autonomous agents, multi-agent teams, chat sessions, RAG pipelines, tool/MCP integrations, safety policies, and CLI-served agent projects.

## Verified package facts

- Distribution name: `upsonic`
- Version distilled here: `0.77.3`
- Python requirement: `>=3.10`
- Console script: `upsonic = upsonic.cli.main:main`
- Top-level import uses lazy loading so `import upsonic` stays light and only loads heavier subsystems when needed.

## Top-level exports

| Export | What it is for | Owning route |
| --- | --- | --- |
| `Task` | Structured task input: description, context, attachments, tools, skills, response format, cache, and policy flags. | agent-runtime |
| `Agent` / `Clanker` | Main execution surface for model calls, tools, skills, memory, policies, streaming, and structured outputs. | agent-runtime |
| `Direct` | Lightweight direct LLM wrapper for model calls without the full Agent tool/memory pipeline. | agent-runtime |
| `Chat` | Stateful chat/session wrapper that binds an Agent to Memory and Storage. | chat-memory-storage |
| `Team` | Multi-agent coordinator with sequential, coordinate, and route modes. | teams-autonomous-prebuilt |
| `KnowledgeBase` | Document/RAG orchestration over sources, loaders, splitters, embeddings, vector DBs, and storage. | knowledge-rag |
| `AutonomousAgent` | Agent subclass with sandboxed filesystem and shell capabilities. | teams-autonomous-prebuilt |
| `PrebuiltAutonomousAgentBase` | Base class for prebuilt autonomous agents that fetch prompt and skill templates. | teams-autonomous-prebuilt |
| `Simulation` | LLM-powered time-series simulation orchestrator. | teams-autonomous-prebuilt |
| `RalphLoop` | Autonomous development loop with requirements, todo, and incremental phases. | teams-autonomous-prebuilt |
| `Graph` | Lower-level graph/runtime primitive for specialized orchestration work. | agent-runtime |

## Architecture map

| Area | Representative modules | Typical workflows | Owner |
| --- | --- | --- | --- |
| Agent execution | `agent/`, `tasks/`, `direct.py`, `graph/`, `run/`, `context/`, `messages/`, `cache/`, `canvas/`, `culture/` | one-shot runs, streaming, structured output, cancellation and runtime control | agent-runtime |
| Model selection | `models/`, `providers/`, `profiles/` | `provider/model` resolution, provider inference, model settings, profile tuning | models-and-providers |
| Tooling | `tools/` | function tools, MCP handlers, agent-as-tool, orchestration, HITL controls | tools-and-mcp |
| Session state | `chat/`, `memory/`, `storage/` | chat history, memory flags, session persistence, backend backends | chat-memory-storage |
| Retrieval | `knowledge_base/`, `embeddings/`, `loaders/`, `text_splitter/`, `vectordb/`, `ocr/` | document ingestion, chunking, retrieval, OCR, vector search | knowledge-rag |
| Multi-agent and autonomous workflows | `team/`, `agent/autonomous_agent/`, `prebuilt/`, `ralph/`, `simulation/` | teams, sandboxed autonomous work, prebuilt agents, long-running loops, simulations | teams-autonomous-prebuilt |
| Governance | `safety_engine/`, `reflection/`, `reliability_layer/`, `eval/`, `integrations/` | policy enforcement, reflection, reliability, tracing, evals | quality-safety-governance |
| Skills | `skills/` | load, validate, cache, and execute reusable agent skills | skills-system |
| CLI / project scaffolding | `cli/`, `interfaces/`, `integrations/` | project bootstrap, config validation, server launch, OpenAPI assembly | project-cli-interfaces |

## Minimal starting patterns

```python
from upsonic import Agent, Task
agent = Agent(model="anthropic/claude-sonnet-4-6")
result = agent.do(Task("Summarize the report"))
```

```python
from upsonic import Direct, Task
result = Direct(model="openai/gpt-4o").do(Task("Write a short answer"))
```

```python
from upsonic import KnowledgeBase
# Build with a vector DB, loaders, and embeddings selected for the task.
```
