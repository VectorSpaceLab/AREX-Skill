# Custom agents

This reference covers the runtime objects used to build profile-driven OASIS agents.

## File-based generators

### `generate_reddit_agent_graph(profile_path, model=None, available_actions=None)`

- Async helper that loads Reddit JSON and returns a populated `AgentGraph`.
- Each JSON object becomes one `SocialAgent`.
- The generator uses `username`, `bio`, and the persona fields to build `UserInfo`.
- Use this when the Reddit profile file already matches the canonical schema.

### `generate_twitter_agent_graph(profile_path, model=None, available_actions=None)`

- Async helper that loads Twitter CSV and returns a populated `AgentGraph`.
- Each CSV row becomes one `SocialAgent`.
- The generator uses `username`, `description`, and `user_char` to build `UserInfo`.
- Use this when the Twitter profile file already matches the canonical schema.

## `AgentGraph`

### Constructor

```python
AgentGraph(backend="igraph", neo4j_config=None)
```

| Parameter | Meaning |
| --- | --- |
| `backend` | `"igraph"` for in-memory graphs, `"neo4j"` for a Neo4j-backed graph. |
| `neo4j_config` | Required when `backend="neo4j"`. Must contain a valid URI, username, and password. |

### Methods

| Method | Purpose |
| --- | --- |
| `add_agent(agent)` | Add one `SocialAgent` to the graph and register it by `agent_id`. |
| `add_edge(agent_id_0, agent_id_1)` | Add a directed follow edge. |
| `remove_agent(agent)` | Remove one agent and its edges. |
| `remove_edge(agent_id_0, agent_id_1)` | Remove a directed follow edge if it exists. |
| `get_agent(agent_id)` | Fetch one agent by id. |
| `get_agents(agent_ids=None)` | Fetch all agents or a selected ordered subset. |
| `get_num_nodes()` | Return the number of agents in the graph. |
| `get_num_edges()` | Return the number of edges in the graph. |
| `visualize(path, ...)` | Render an igraph visualization to a file path. |
| `close()` | Close the Neo4j driver when the backend uses Neo4j. |

Extra helpers exist in the implementation, but the methods above are the ones most useful for profile-driven agent work.

### Graph notes

- The in-memory backend is the safest default for profile creation and validation.
- Use zero-based, contiguous ids when you want graph edges and agent lookups to stay aligned with insertion order.
- `visualize(...)` is only available on the igraph backend.
- `close()` is a no-op for igraph and only matters for Neo4j.

## `SocialAgent`

### Constructor

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

| Parameter | Meaning |
| --- | --- |
| `agent_id` | Unique integer id for the agent. |
| `user_info` | `UserInfo` with the agent identity and profile payload. |
| `user_info_template` | Optional `TextPrompt` for custom prompt construction. |
| `channel` | Optional social channel; a default channel is created when omitted. |
| `model` | CAMEL model backend, list of backends, or `ModelManager`. |
| `agent_graph` | Optional graph reference for graph-aware actions. |
| `available_actions` | Action filter for the agent. Accepts `ActionType` values or matching action-name strings. |
| `tools` | External CAMEL tools or plain callables. |
| `max_iteration` | Number of reasoning/tool iterations allowed when the agent acts. |
| `interview_record` | Whether interview prompts and responses are stored in memory. |

### SocialAgent behavior

- If `user_info_template` is omitted, the default prompt comes from `UserInfo.recsys_type`.
- If `available_actions` is omitted, the agent gets the full built-in social action set.
- Unsupported action names are warned about and filtered out.
- External tools are appended to the social-action tools, not substituted for them.
- Use `max_iteration > 1` when you want the agent to keep using tools after the first model response.

## `UserInfo`

### Default prompt behavior

| `recsys_type` | Default prompt |
| --- | --- |
| `"twitter"` or anything other than `"reddit"` | Twitter-style prompt using `name` and `user_profile`. |
| `"reddit"` | Reddit-style prompt using `name`, `user_profile`, `gender`, `age`, `mbti`, and `country`. |

### Custom prompt validation

`to_custom_system_message(user_info_template)` compares `TextPrompt.key_words` with `UserInfo.profile.keys()`.

- Missing keys raise a `ValueError`.
- Extra keys trigger a warning.
- The template is formatted with the flat `profile` dictionary, so nested lookups are not supported by the built-in validator.

## CAMEL external toolkits

You can add any CAMEL toolkit or custom tool to `SocialAgent.tools`.

```python
from camel.toolkits import FunctionTool
from camel.tools import SearchToolkit, SymPyToolkit

# Multiple toolkit tools
math_tools = SymPyToolkit().get_tools()

# Single callable tool
search_tool = SearchToolkit().search_duckduckgo

# Custom function tool
custom_tool = FunctionTool(my_custom_function)
```

Guidance:

- Keep custom tool functions documented and type-annotated.
- Add tools when you need external computation or retrieval in addition to social actions.
- If the agent should call tools more than once in a single turn, raise `max_iteration`.

## Optional Neo4j backend

- Build the graph with `AgentGraph(backend="neo4j", neo4j_config=Neo4jConfig(...))`.
- `Neo4jConfig.is_valid()` only checks that URI, username, and password are present.
- The Neo4j service must still be reachable for graph construction to succeed.
- Visualization is not supported on the Neo4j backend.
