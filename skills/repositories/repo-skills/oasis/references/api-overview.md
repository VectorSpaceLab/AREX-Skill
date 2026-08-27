# OASIS API overview

Use this reference for the top-level package surface and high-level object relationships. Route detailed tasks to sub-skills for workflows, profiles, platform actions, and legacy experiments.

## Package identity

- Distribution: `camel-oasis`
- Import name: `oasis`
- Verified package version for this skill: `0.2.5`
- Python support from package metadata: `>=3.10,<3.12`

Install for normal use:

```bash
pip install camel-oasis
```

For a local checkout or development install:

```bash
pip install -e .
```

The package depends on CAMEL, pandas, igraph, cairocffi, Neo4j client, sentence-transformers/torch-related packages, OpenAPI tooling, and other support libraries. Some optional workflows need provider credentials, local model servers, model downloads, or Neo4j service credentials.

## Public exports

The root `oasis` module exports:

| Export | Role |
| --- | --- |
| `make` | Construct an `OasisEnv` from an `AgentGraph` and a default or custom platform. |
| `Platform` | Low-level social platform with SQLite storage and action dispatch. |
| `ActionType` | Enum of social, group, report, product, recommendation, and infrastructure actions. |
| `DefaultPlatformType` | Enum with `TWITTER` and `REDDIT` presets. |
| `ManualAction` | Dataclass for explicit action type plus argument dict. |
| `LLMAction` | Marker that tells an agent to choose an action through its LLM/tool-calling model. |
| `AgentGraph` | In-memory igraph or optional Neo4j-backed graph of `SocialAgent` objects. |
| `SocialAgent` | CAMEL `ChatAgent` subclass that owns OASIS social actions and optional external tools. |
| `UserInfo` | Agent identity/profile dataclass used to build system prompts. |
| `generate_reddit_agent_graph` | Async JSON-profile graph generator. |
| `generate_twitter_agent_graph` | Async CSV-profile graph generator. |
| `print_db_contents` | Utility for printing SQLite DB contents. |

## Verified signatures

```python
make(*args, **kwargs)
```

`make` returns the environment wrapper and forwards arguments to `OasisEnv`.

```python
AgentGraph(backend="igraph", neo4j_config=None)
```

```python
SocialAgent(
    agent_id,
    user_info,
    user_info_template=None,
    channel=None,
    model=None,
    agent_graph=None,
    available_actions=None,
    tools=None,
    max_iteration=1,
    interview_record=False,
)
```

```python
Platform(
    db_path,
    channel=None,
    sandbox_clock=None,
    start_time=None,
    show_score=False,
    allow_self_rating=True,
    recsys_type="reddit",
    refresh_rec_post_count=1,
    max_rec_post_len=2,
    following_post_count=3,
    use_openai_embedding=False,
)
```

## Object relationship

1. Build an `AgentGraph` manually or from profile files.
2. Each graph node is a `SocialAgent` with `UserInfo`, a CAMEL model backend, optional external tools, and an allowed action set.
3. Build an environment with `oasis.make(agent_graph=..., platform=..., database_path=...)`.
4. `env.reset()` starts the platform loop and signs up agents in the SQLite DB.
5. `env.step(actions)` updates recommendations, runs manual and/or LLM actions, and writes platform state and traces.
6. `env.close()` stops the platform loop and closes the DB.

## Important behavior checked during skill generation

- `ManualAction` fields are `action_type` and `action_args`; older examples or docs may use stale names such as `action` and `args`.
- Current `SocialAgent(model=None)` construction goes through CAMEL's default model setup and can require a non-empty provider key even if no real `LLMAction` is executed. The bundled manual smoke helper uses a non-secret placeholder only to construct agents without provider calls.
- The default Twitter platform uses `twhin-bert`, which may require optional model downloads or torch/CUDA resources. Use `REDDIT` or a custom platform with `recsys_type="random"`/`"reddit"` for tiny local checks.
- CAMEL `0.2.78` can fail to import with `mcp>=2` because `FastMCP` is no longer available at the path CAMEL imports. Pin `mcp<2` or use a compatible CAMEL release if this appears.

## Route map

- Need profiles, `AgentGraph`, `SocialAgent`, `UserInfo`, custom prompts, toolkits, or validation? Use `sub-skills/agent-profiles/SKILL.md`.
- Need to run a simulation, adapt the environment lifecycle, or handle model backends/costs? Use `sub-skills/simulation-workflows/SKILL.md`.
- Need action arguments, `Platform`, `RecsysType`, SQLite tables, traces, or DB inspection? Use `sub-skills/platform-actions/SKILL.md`.
- Need legacy experiment YAMLs, generated-user notes, result analysis, visualizations, or large-scale run triage? Use `sub-skills/experiments-analysis/SKILL.md`.
