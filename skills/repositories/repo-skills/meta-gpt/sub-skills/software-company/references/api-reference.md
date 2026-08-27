# Software Company API Reference

## Package and Console Entry

| Item | Value / behavior |
| --- | --- |
| Distribution | `metagpt==1.0.0` |
| Python requirement | `>=3.9,<3.12` |
| Console script | `metagpt=metagpt.software_company:app` |
| CLI framework | Typer app with completion disabled and local variables hidden in pretty exceptions |
| Deprecated module | `metagpt.startup` is deprecated; the startup implementation is in `metagpt.software_company` |

## CLI Entry Point

`metagpt` runs `metagpt.software_company.startup(...)`.

| Parameter | Default | Notes |
| --- | --- | --- |
| `idea` | `None` | Positional one-line requirement such as `Create a 2048 game`; omitted idea prints a missing-argument message unless `--init-config` is used. |
| `--investment` | `3.0` | Dollar budget for the team cost manager. |
| `--n-round` | `5` | Maximum simulation rounds. |
| `--code-review/--no-code-review` | `--code-review` | Boolean pair exposed by Typer. Current default software-company role list is DI/MGX-oriented; legacy engineer code-review hiring is commented in source. |
| `--run-tests/--no-run-tests` | `--no-run-tests` | Enables QA intent; source comments note QA historically needed at least 8 rounds. |
| `--implement/--no-implement` | `--implement` | Controls implementation intent; legacy conditional hiring code is commented in source. |
| `--project-name` | `""` | Unique project name such as `game_2048`; used in config update and workspace selection. |
| `--inc/--no-inc` | `--no-inc` | Incremental mode for existing repositories. |
| `--project-path` | `""` | Existing project directory for incremental work or explicit output context. |
| `--reqa-file` | `""` | Source file name for rewriting quality-assurance code. |
| `--max-auto-summarize-code` | `0` | Maximum automatic `SummarizeCode` invocations; `-1` means unlimited. |
| `--recover-path` | `None` | Existing serialized storage path; must exist and end with `team`. |
| `--init-config/--no-init-config` | `--no-init-config` | Creates or replaces user config at `~/.metagpt/config2.yaml`, backing up an existing file with `.bak`. |

## `generate_repo(...)`

Import:

```python
from metagpt.software_company import generate_repo
```

Signature:

```python
generate_repo(
    idea,
    investment=3.0,
    n_round=5,
    code_review=True,
    run_tests=False,
    implement=True,
    project_name="",
    inc=False,
    project_path="",
    reqa_file="",
    max_auto_summarize_code=0,
    recover_path=None,
)
```

Behavior:

1. Imports global config and updates it with `project_path`, `project_name`, `inc`, `reqa_file`, and `max_auto_summarize_code`.
2. Creates a `Context(config=config)`.
3. Without `recover_path`, creates a `Team(context=ctx)` and hires `TeamLeader`, `ProductManager`, `Architect`, `Engineer2`, and `DataAnalyst`.
4. With `recover_path`, validates that the path exists and ends in `team`, deserializes `Team.deserialize(stg_path=..., context=ctx)`, and uses the recovered `company.idea`.
5. Calls `company.invest(investment)` and `asyncio.run(company.run(n_round=n_round, idea=idea))`.
6. Returns `ctx.kwargs.get("project_path")`.

Failure surfaces:

- Bad recovery path raises `FileNotFoundError("... not exists or not endswith `team`")`.
- Missing `team.json` during deserialization raises a recovery metadata `FileNotFoundError`.
- Invalid or placeholder config can fail during config loading or first LLM call.
- Running inside an already-running event loop can conflict with `asyncio.run(...)`; use lower-level async `Team` APIs in notebooks or async apps.

## `Team`

Import:

```python
from metagpt.team import Team
```

Important fields and methods:

| API | Purpose |
| --- | --- |
| `Team(context=None, env=None, roles=[...], investment=10.0, use_mgx=True)` | Creates an environment-backed team. Defaults to `MGXEnv` when no env is provided and `use_mgx=True`; otherwise uses `Environment`. |
| `hire(roles: list[Role])` | Adds roles to the team environment. |
| `invest(investment: float)` | Sets `self.investment` and `cost_manager.max_budget`. |
| `run_project(idea, send_to="")` | Stores `idea` and publishes the user requirement as a `Message`. |
| `start_project(...)` | Deprecated wrapper around `run_project(...)`. |
| `async run(n_round=3, idea="", send_to="", auto_archive=True)` | Publishes an idea if provided, runs the environment until idle, rounds are exhausted, or budget is exceeded, then archives environment state. |
| `serialize(stg_path=None)` | Writes team metadata under a `team` storage directory. |
| `deserialize(stg_path, context=None)` | Reconstructs team and context from `team.json`. |

Budget behavior: before each environment round, `_check_balance()` raises `NoMoneyException` if total cost has reached the investment cap.

## `Action`

Import:

```python
from metagpt.actions import Action
```

Important behavior:

- Subclass `Action` and implement `async run(...)` for custom behavior.
- `name` defaults to the class name when omitted.
- `instruction=...` can initialize an `ActionNode` for simple node-backed actions.
- `_aask(prompt, system_msgs=None)` delegates to the configured LLM and should be treated as an API-spending call.
- `llm_name_or_type` can select a named/model-specific private LLM configuration from `models` in `config2.yaml`; `None` uses the default `llm` config.
- `set_prefix(...)` updates both action prefix and the action LLM's system prompt.

## `Role` and `RoleReactMode`

Imports:

```python
from metagpt.roles.role import Role, RoleReactMode
```

Important fields:

| Field | Purpose |
| --- | --- |
| `name` | Role display/routing name, such as `Alice`. |
| `profile` | Role profile, such as `SimpleCoder`. |
| `goal` | Goal text included in the role prefix. |
| `constraints` | Constraint text included in the role prefix. |
| `actions` | List of action classes or action instances. |
| `rc` | `RoleContext` containing memory, todo, watch set, state, and message buffer. |
| `is_human` | Uses a human provider when action initialization allows it. |

Important methods:

| API | Purpose |
| --- | --- |
| `set_actions([ActionClassOrInstance, ...])` | Resets and initializes actions, states, context, LLM, and prefix. |
| `set_action(action)` | Convenience wrapper for one action. |
| `_set_react_mode(react_mode, max_react_loop=1, auto_run=True)` | Chooses `react`, `by_order`, or `plan_and_act`. |
| `_watch([ActionClass, ...])` | Watches messages caused by those actions during observation. |
| `get_memories(k=0)` | Returns all or recent role memories. |
| `async run(with_message=None)` | Observes messages, thinks, acts, publishes response, then resets todo. |
| `publish_message(msg)` / `put_message(msg)` | Send to environment or local role buffer. |

`RoleReactMode` values:

- `react`: LLM chooses the next action during `_think`; bounded by `max_react_loop`.
- `by_order`: executes actions in their configured order; useful for code-then-run/test flows.
- `plan_and_act`: builds a plan and executes task sequence through the planner.

## `Message`

Import:

```python
from metagpt.schema import Message
```

Common custom-role shape:

```python
Message(
    content="...",
    role=self.profile,
    cause_by=type(todo),
    sent_from=self.name,
    send_to={"OtherRoleName"},
)
```

Notes:

- `cause_by` is central to `_watch(...)` routing.
- `send_to` can target named roles; a special self-route is normalized by `Role.publish_message(...)`.
- Roles store observed and produced messages in memory when memory is enabled.

## `ProjectRepo`

Import:

```python
from metagpt.utils.project_repo import ProjectRepo
```

Purpose:

- Wraps a generated project root with document, resource, test, output, and source repositories.
- `ProjectRepo(path)` accepts a path or `GitRepository`.
- `.docs` includes repositories for PRD, system design, tasks, code summaries, graph repo, class view, and code plan/change.
- `.resources` includes rendered artifacts for analysis, design, PRD, task, summaries, and graph outputs.
- `.tests` and `.test_outputs` point to generated test files and their execution outputs.
- `.code_files_exists()` probes whether generated source files exist.
- `.with_src_path(path)` sets the source repository path before `.srcs` access.
- `ProjectRepo.search_project_path(filename)` walks upward to find a git root.
