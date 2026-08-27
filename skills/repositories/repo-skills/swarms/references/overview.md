# Swarms package overview

## Public surface at a glance

Swarms is a multi-agent orchestration framework. The top-level package exports the main runtime classes and helper utilities through `swarms.__init__`, so users can usually start from `from swarms import ...`.

### Common entry points

- `Agent`: one autonomous agent with tools, memory, prompt caching, MCP, and fallback support.
- `SequentialWorkflow`, `ConcurrentWorkflow`, `AgentRearrange`, `GraphWorkflow`, `SwarmRouter`: orchestration and routing.
- `MixtureOfAgents`, `HierarchicalSwarm`, `GroupChat`, `MajorityVoting`, `CouncilAsAJudge`, `DebateWithJudge`, `RoundRobinSwarm`, `PlannerWorkerSwarm`, `HeavySwarm`, `BatchedGridWorkflow`, `MultiAgentRouter`: advanced swarm strategies.
- `BaseTool`, `MCPManager`, `MCPConnection`, `MCPOAuthConfig`: tool schema and MCP helpers.
- `Artifact`, `Conversation`, `SkillsManager`, `ContextCompressor`, `AgentMarketplaceHandler`: single-agent support objects.

### Environment facts

- Package version captured here: `14.0.0`.
- Supported Python floor in metadata: `>=3.10`.
- CLI entry point: `swarms`.
- Optional backend extras in the source tree: `graphviz`, `rustworkx`.

### Route selection hints

- Use `single-agent` when the user is tuning one agent or its support objects.
- Use `cli-loaders` when the request starts from a command, YAML, or markdown file.
- Use `multi-agent-workflows` when the request combines multiple agents into a swarm.
- Use `tools-mcp` when the user is converting callables to schemas or connecting MCP servers.

### What to expect from the subskills

Each subskill is self-contained and includes its own workflow notes, troubleshooting, and reusable scripts. Prefer the subskill that owns the exact workflow rather than the broadest one that merely mentions the same class names.
