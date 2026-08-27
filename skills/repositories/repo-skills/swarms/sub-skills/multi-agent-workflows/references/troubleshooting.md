# Multi-agent troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Workflow constructor rejects the agents list | No agents were passed or the list is empty | Create at least one agent, or more for workflows that require collaboration. |
| `AgentRearrange` fails on a flow string | Flow names do not match the registered agents | Check spelling and ensure every branch name exists. |
| `GroupChat` does not speak | One or more agents are missing `RESPOND_TOOL` | Attach the forced respond tool to every group-chat participant. |
| A router picks the wrong style | `swarm_type` or `rearrange_flow` does not match the task | Choose the swarm class directly or provide a more specific flow string. |
| `GraphWorkflow` optional backend code is unavailable | `graphviz` or `rustworkx` missing | Install the optional dependency only if the workflow needs that backend. |
| Concurrent output looks truncated or interleaved | The task is network-bound and multiple agents are running at once | Reduce concurrency or use a sequential workflow when order matters. |
| A consensus workflow never stabilizes | The task is too open-ended or the loop count is too high | Use a smaller `max_loops` or a more explicit task prompt. |
| `SwarmRouter` cannot create the requested swarm | The selected `swarm_type` is invalid or lacks required supporting parameters | Verify the router type and pass any required flow, judge, or variant settings. |

## Recovery order

1. Verify the exact swarm class and its required constructor inputs.
2. Check flow strings, agent names, and required special tools.
3. Confirm optional backends only when the chosen workflow truly needs them.
4. Use a fake-agent smoke check before blaming provider credentials or model behavior.
