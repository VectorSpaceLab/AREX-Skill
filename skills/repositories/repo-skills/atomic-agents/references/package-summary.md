# Package Summary

Atomic Agents is a monorepo with four public-facing surfaces and one maintainer surface:

| Surface | What it is | Main user signal |
| --- | --- | --- |
| `atomic-agents/` | The core Python framework package, published as `atomic-agents` | build a typed agent, custom schema, history, hooks, multimodal prompt handling, or token counting |
| `atomic-assembler/` | The CLI/TUI package that exposes the `atomic` command | browse and download Atomic Forge tools from the terminal |
| `atomic-examples/` | Runnable example projects and recipes | learn a workflow by reading or adapting a concrete application |
| `atomic-forge/` | Downloadable tool packages plus authoring guides | choose a tool family or understand how to package a new tool |
| `docs/` and `guides/` | Public docs, API pages, and how-to guides | cross-check behavior, terminology, and troubleshooting |

## Core terminology

- **AtomicAgent**: the main schema-driven chat agent class.
- **BaseIOSchema**: the Pydantic base class for structured inputs and outputs. Every subclass needs a non-empty docstring.
- **ChatHistory**: the built-in in-memory history implementation; custom history backends must preserve the `copy()` contract.
- **SystemPromptGenerator**: the structured prompt builder used by default when the user does not provide a custom generator.
- **BaseTool / BaseResource / BasePrompt**: the typed interfaces for tool, resource, and prompt components.
- **Atomic Forge**: the downloadable tool collection that ships as separate tool packages, not as bundled framework dependencies.
- **Atomic Assembler**: the `atomic` CLI/TUI used to browse and download Forge tools.
- **MCP**: the Model Context Protocol connector surface used to discover and call remote tools, resources, and prompts.

## Public package facts

- Published package name: `atomic-agents`
- Current repo version: `2.10.0`
- Required Python version in this snapshot: `>=3.12`
- Main entry point: `atomic` from `atomic_assembler.main:main`
- Top-level import surface: `AtomicAgent`, `AgentConfig`, `BasicChatInputSchema`, `BasicChatOutputSchema`, `BaseIOSchema`, `BaseTool`, `BaseToolConfig`, `VideoURL`
- Context import surface: `ChatHistory`, `BaseChatHistory`, `SystemPromptGenerator`, `BaseDynamicContextProvider`
- Utility import surface: `TokenCounter`, `TokenCountResult`, `TokenCountError`, `format_tool_message`
- MCP import surface: `MCPFactory`, `MCPDefinitionService`, `SchemaTransformer`, `fetch_mcp_tools`, `fetch_mcp_resources`, `fetch_mcp_prompts`

## When to read this file

Read this file first if you need a fast monorepo map, an install or import reminder, or a compact description of which subskill owns which surface.
