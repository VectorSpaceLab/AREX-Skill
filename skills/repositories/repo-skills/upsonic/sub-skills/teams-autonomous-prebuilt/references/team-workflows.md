# Team Workflows

## Verified shape

`Team(entities=None, tasks=None, name=None, role=None, goal=None, model=None, response_format=str, ask_other_team_members=False, mode='sequential', leader=None, router=None, memory=None, skills=None, debug=False, debug_level=1, agents=None, print=None, team_id=None, team_usage_id=None)`

## Common modes

| Mode | Meaning |
| --- | --- |
| `sequential` | Run team members in order. |
| `coordinate` | Use a leader/coordinator pattern. |
| `route` | Route tasks to the best agent for the job. |

## Workflow notes

- Keep `Task` and single-agent run logic in the agent-runtime route.
- Use `Team.as_mcp()` only when the user wants a protocol surface.
- Use `Team.do()` for team-level execution and `Team.multi_agent_async()` for richer async fan-out.

## Typical pattern

```python
from upsonic import Agent, Team, Task

team = Team(agents=[Agent(), Agent()], tasks=[Task('Draft a plan')], mode='sequential')
team.do()
```
