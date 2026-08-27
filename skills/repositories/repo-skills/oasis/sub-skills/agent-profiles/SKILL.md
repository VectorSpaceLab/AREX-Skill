---
name: agent-profiles
description: "Create, customize, and validate OASIS agent graphs, social agents,
  and profile files."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Agent Profiles

Use this sub-skill when you need to turn profile files into populated agent graphs or hand-built social agents.

## Use for
- `generate_reddit_agent_graph(...)` and `generate_twitter_agent_graph(...)`
- `AgentGraph` construction and graph edits
- `SocialAgent` setup with custom `UserInfo`, prompts, and toolkits
- optional Neo4j-backed graphs
- profile validation before generation

## Do not use for
- environment lifecycle, `reset`/`step`/`close`, or provider execution → simulation-workflows
- action-argument matrices and database side effects → platform-actions
- legacy generator or visualization experiments → experiments-analysis

## Recommended flow
1. Check the file format in [profile-data-formats.md](references/profile-data-formats.md).
2. Validate the input with [validate_oasis_profiles.py](scripts/validate_oasis_profiles.py).
3. Build or customize agents with [custom-agents.md](references/custom-agents.md).
4. If something fails, open [troubleshooting.md](references/troubleshooting.md).

## What success looks like
- a valid Reddit or Twitter profile file
- a populated `AgentGraph`
- a custom `SocialAgent` with the right prompt, actions, and tools
- a Neo4j graph only when credentials and service are available
