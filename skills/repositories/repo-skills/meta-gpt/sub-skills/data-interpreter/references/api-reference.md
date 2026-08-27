# Data Interpreter API Reference

This reference captures the DI roles and actions most useful for future agents. Constructor signatures should be verified with `scripts/di_import_check.py` in the target environment because optional dependencies and configuration can affect importability.

## Primary Roles

| Class | Module | Use For | Important Fields and Defaults |
| --- | --- | --- | --- |
| `DataInterpreter` | `metagpt.roles.di.data_interpreter` | Classic plan/code/execute data analysis and benchmark tasks | `name="David"`, `profile="DataInterpreter"`, `auto_run=True`, `use_plan=True`, `use_reflection=False`, `tools=[]`, `react_mode="plan_and_act"`, `max_react_loop=10` |
| `RoleZero` | `metagpt.roles.di.role_zero` | Dynamic react role with command/tool parsing | `name="Zero"`, `profile="RoleZero"`, `react_mode="react"`, `max_react_loop=50`, `tools=[]`, `memory_k=200`, `use_summary=True` |
| `DataAnalyst` | `metagpt.roles.di.data_analyst` | RoleZero plus data/browser/search/editor/code execution | `profile="DataAnalyst"`, `use_reflection=True`, `tools=["Plan", "DataAnalyst", "RoleZero", "Browser", "Editor:write,read,similarity_search", "SearchEnhancedQA"]` |
| `SWEAgent` | `metagpt.roles.di.swe_agent` | Dynamic issue fixing with bash/browser/git tools | `profile="Issue Solver"`, `tools=["Bash", "Browser:goto,scroll", "RoleZero", "git_create_pull"]`, `max_react_loop=40`, `run_eval=False` |
| `Engineer2` | `metagpt.roles.di.engineer2` | Engineering, app/game/web development, code review, deployment workflows | `profile="Engineer"`, tools include `Plan`, `Editor`, `Terminal:run_command`, `Browser:goto,scroll`, `SearchEnhancedQA`, `Engineer2`, `CodeReview`, `ImageGetter`, `Deployer`; `max_react_loop=40` |
| `TeamLeader` | `metagpt.roles.di.team_leader` | Team delegation and role message routing | `profile="Team Leader"`, `tools=["Plan", "RoleZero", "TeamLeader"]`, `max_react_loop=3`, `use_summary=False` |

## DataInterpreter Patterns

Basic usage:

```python
import asyncio
from metagpt.roles.di.data_interpreter import DataInterpreter

async def main():
    role = DataInterpreter()
    await role.run("Run data analysis on sklearn Iris dataset, include a plot")

asyncio.run(main())
```

Reflection/tool usage:

```python
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.tools.tool_recommend import TypeMatchToolRecommender

role = DataInterpreter(
    use_reflection=True,
    tool_recommender=TypeMatchToolRecommender(tools=["<all>"]),
)
await role.run(requirement)
```

React mode with a named tool:

```python
role = DataInterpreter(react_mode="react", tools=["Browser"])
await role.run("Open the docs site and summarize the supported LLM APIs. Don't write all code in one response.")
```

Custom registered tool:

```python
from metagpt.tools.tool_registry import register_tool

@register_tool()
def magic_function(arg1: str, arg2: int) -> dict:
    return {"arg1": arg1 * 3, "arg2": arg2 * 5}

role = DataInterpreter(tools=["magic_function"])
await role.run("Call magic_function with arg1 'A' and arg2 2, then report the result.")
```

Key behavior:

- `DataInterpreter.set_plan_and_tool()` forces `use_plan` from `react_mode == "plan_and_act"` and installs `WriteAnalysisCode` as the action.
- `_write_and_exec_code()` retries generated code up to three times, calling `WriteAnalysisCode.run(...)` then `ExecuteNbCode.run(code)`.
- `use_reflection=True` matters only after a failed attempt (`counter > 0`).
- `_check_data()` can run `CheckData` after finished tasks of type `DATA_PREPROCESS`, `FEATURE_ENGINEERING`, or `MODEL_TRAIN`.
- `plan_and_act` mode terminates the notebook executor after completion or exception.

## RoleZero Patterns

`RoleZero` uses a react cycle:

1. Observe user or team messages.
2. Quick-think for short answers or search intents.
3. Build plan status and available command schemas.
4. Ask the LLM for tool commands.
5. Parse commands, de-duplicate exclusive commands, execute mapped tools, and add outputs to memory.
6. Stop on `end`, max loop, or no todo.

Built-in command map includes:

- `Plan.append_task`, `Plan.reset_task`, `Plan.replace_task`.
- `RoleZero.ask_human`, `RoleZero.reply_to_human`.
- `SearchEnhancedQA.run` when search is enabled in config.
- Browser actions: `click`, `close_tab`, `go_back`, `go_forward`, `goto`, `hover`, `press`, `scroll`, `tab_focus`, `type`.
- Editor actions: `append_file`, `create_file`, `edit_file_by_replace`, `find_file`, `goto_line`, `insert_content_at_line`, `open_file`, `read`, `scroll_down`, `scroll_up`, `search_dir`, `search_file`, `similarity_search`, `write`.

Special commands include `Plan.finish_current_task`, `end`, `Terminal.run_command`, and `RoleZero.ask_human`.

## DataAnalyst Patterns

`DataAnalyst` is registered as a tool provider for `DataAnalyst.write_and_exec_code`.

```python
from metagpt.roles.di.data_analyst import DataAnalyst

analyst = DataAnalyst()
await analyst.run("Analyze this CSV and create a short report; ask before writing files.")
```

Direct code tool behavior:

- `write_and_exec_code(instruction="")` requires a current planner task; otherwise it returns `No current_task found now. Please use command Plan.append_task to add a task first.`
- It initializes notebook code once, builds plan status, recommends custom tools, optionally checks updated data, retries generated code up to three times, and updates the current task result on success.
- `custom_tools` defaults to `web scraping`, `Terminal`, and limited editor operations; check side effects before allowing them.

## SWEAgent and Engineer2 Patterns

Use these roles for repository issue fixing or app/game/web development only with user approval for file and command side effects.

```python
from metagpt.roles.di.swe_agent import SWEAgent

agent = SWEAgent()
await agent.run("Resolve this issue in the current repository. Ask before committing or pushing.")
```

```python
from metagpt.roles.di.engineer2 import Engineer2

engineer = Engineer2(run_eval=False)
await engineer.run("Create a small app in an isolated workspace. Ask before deployment.")
```

Important differences:

- `SWEAgent` maps `Bash.run` and `git_create_pull`; `run_eval=True` can parse diffs for benchmark submission behavior.
- `Engineer2` maps `Terminal.run_command`, editor operations, code review, image getter, deployer, and `Engineer2.write_new_code`.
- `Engineer2.write_new_code(path, file_description="")` writes a new code file after fixing relative paths against the editor workdir.
- Both can modify repositories; do not run on user checkouts without explicit scope and approval.

## TeamLeader Patterns

`TeamLeader` routes tasks to team members in an environment.

- `publish_team_message(content, send_to)` sends a user-style message to a named role and pauses the TeamLeader.
- Team member names matter; include required paths, constraints, environment notes, and full task context because the recipient receives the message as its sole instruction.
- `finish_current_task()` marks the current planner task finished.

## DI Actions

| Action | Module | Purpose | Runtime Notes |
| --- | --- | --- | --- |
| `WriteAnalysisCode` | `metagpt.actions.di.write_analysis_code` | Generate Python code from user requirement, plan status, tool info, and working memory | Calls LLM; parses Python code from response; optional reflection prompt after failure |
| `CheckData` | `metagpt.actions.di.write_analysis_code` | Generate code to inspect updated data after completed data tasks | Runs through notebook executor when task types match |
| `ExecuteNbCode` | `metagpt.actions.di.execute_nb_code` | Execute Python or markdown in a notebook and collect outputs | Starts kernel lazily; default timeout `600`; writes `code.ipynb`; terminate after use |
| `WritePlan` | `metagpt.actions.di.write_plan` | Ask LLM for task JSON plan from context and available task types | Parses fenced JSON; plan updates are validated by helper functions |
| `RunCommand` | `metagpt.actions.di.run_command` | Minimal action tag for RoleZero command outputs | Used as a cause marker for dynamic tool execution |
| `AskReview` | `metagpt.actions.di.ask_review` | Review/confirmation support constants and action | Mostly internal and less common in current DI flow |

## ExecuteNbCode API

Constructor:

```python
from metagpt.actions.di.execute_nb_code import ExecuteNbCode
executor = ExecuteNbCode(timeout=600)
```

Methods and behavior:

- `await executor.run(code, language="python") -> tuple[str, bool]` executes Python and returns parsed output plus success flag.
- `await executor.run(markdown, language="markdown")` stores markdown and returns it with success `True`.
- `await executor.init_code()` runs warning/log suppression initialization once.
- `await executor.terminate()` shuts down kernel manager/client resources.
- `await executor.reset()` terminates, sleeps briefly, rebuilds, and resets the client.
- `parse_outputs(...)` filters MetaGPT logs/warnings, handles image displays, recognizes coroutine-not-awaited output, truncates very long output, and preserves exception tails.

## Tool Recommenders

DI examples use two recommender styles:

- `BM25ToolRecommender(tools=...)` is installed automatically when `tools` is set and `tool_recommender` is omitted.
- `TypeMatchToolRecommender(tools=["<all>"])` appears in benchmark runners to expose all registered tools to a type matcher.

Use named tools where possible. `"<all>"` should be treated as a broad opt-in because it may allow network, file, browser, terminal, image, or external service tools.

## Safe Import Diagnostics

The bundled `scripts/di_import_check.py` imports modules and inspects signatures without instantiating roles, running LLM calls, creating notebook kernels, or executing arbitrary code. It is the preferred first check for errors such as placeholder API keys in `config2.yaml`, missing optional dependencies, or version drift.
