# Data Interpreter Workflows

This reference summarizes how to use MetaGPT Data Interpreter (DI) and RoleZero-family roles without relying on the original repository examples at runtime. DI workflows usually call an LLM, generate Python or tool commands, and execute code; treat them as interactive/expensive tasks, not smoke tests.

## Classic DataInterpreter Quick Start

Use `DataInterpreter` for single-agent data analysis, modeling, plotting, math, and generated-code workflows.

```python
import asyncio
from metagpt.roles.di.data_interpreter import DataInterpreter

async def main():
    requirement = "Run data analysis on sklearn Iris dataset, include a plot"
    role = DataInterpreter()
    result = await role.run(requirement)
    print(result)

asyncio.run(main())
```

Common constructor choices:

- `DataInterpreter()` uses `react_mode="plan_and_act"`, `auto_run=True`, `use_plan=True`, `use_reflection=False`, and a notebook executor.
- `DataInterpreter(auto_run=False)` lets the planner ask for confirmation before automatically continuing tasks.
- `DataInterpreter(use_reflection=True)` enables a reflection retry after a generated-code failure; the first code attempt is still non-reflective.
- `DataInterpreter(react_mode="react")` skips the plan-and-act loop and uses repeated think/act cycles.
- `DataInterpreter(tools=["<all>"])` or a named tool list asks DI to recommend/use registered tools; confirm tool prerequisites and side effects first.

## Data Analysis and Modeling Prompts

DI performs best when the user requirement names the target, metrics, data paths, and output expectations. Include instructions to print key variables for multi-step analysis so later generated code has feedback.

Useful prompt ingredients:

- Dataset purpose and target column, such as `Survived`, `SalePrice`, `target`, or `Class`.
- Train/eval paths with quoted absolute or workspace-relative paths available to the sandbox.
- Required metric, such as accuracy, RMSE on log sale price, AUC, F1 score, or RMSLE.
- Required visible outputs, such as plots, model accuracy, saved CSV/XLSX, or printed intermediate shapes/columns.
- Permission and limits for package installs, network access, file writes, and long-running model training.

Safe adaptation pattern:

```python
import asyncio
from metagpt.roles.di.data_interpreter import DataInterpreter

async def main(train_path: str, eval_path: str):
    requirement = f"""
    This is a Titanic survival dataset. The target column is Survived.
    Perform data analysis, preprocessing, feature engineering, and modeling.
    Report accuracy on the eval data.
    Train data path: '{train_path}', eval data path: '{eval_path}'.
    Print key columns, row counts, and validation metric before final answer.
    """
    role = DataInterpreter(use_reflection=True)
    await role.run(requirement)

asyncio.run(main("data/di_dataset/ml_benchmark/04_titanic/split_train.csv", "data/di_dataset/ml_benchmark/04_titanic/split_eval.csv"))
```

## Benchmark Task Scripts

The original DI benchmark runners build requirements from task dictionaries and then call `DataInterpreter(use_reflection=..., tool_recommender=TypeMatchToolRecommender(tools=["<all>"]))`. They are intentionally not bundled here because they run LLM/code workflows and require downloaded datasets.

Equivalent structure for safe planning:

1. Validate `task_name` against `references/data-formats.md`.
2. Validate `data_dir` contains `di_dataset/ml_benchmark` or `di_dataset/open_ended_tasks` as appropriate.
3. Format the requirement string using `data_dir`.
4. Decide whether `use_reflection=True` is worth the additional LLM cost.
5. Warn that `tools=["<all>"]` may expose browser, editor, terminal, image, OCR, and network tools depending on the environment.
6. Run only after explicit user approval for LLM calls and generated-code execution.

ML benchmark style:

```python
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.tools.tool_recommend import TypeMatchToolRecommender

role = DataInterpreter(
    use_reflection=True,
    tool_recommender=TypeMatchToolRecommender(tools=["<all>"]),
)
await role.run(requirement)
```

Open-ended task style is the same constructor pattern but tasks may require OCR, browser, Selenium/WebDriver, Stable Diffusion service URLs, email credentials, `rembg`, `pyxel`, or external network access. Mark those as prerequisites/skips unless the user supplies and authorizes them.

## Open-Ended Task Adaptation

For open-ended DI tasks, rewrite the prompt so secrets and service endpoints are not embedded in stored code or logs. Prefer placeholders and environment variables:

- Email reply tasks: never paste account/password into a prompt. Ask the user to provide a secure credential mechanism, define allowed actions, and disable automatic sending until reviewed.
- Stable Diffusion tasks: require an explicit `sd_url` service endpoint and a safe output directory.
- Browser/Selenium page imitation: require browser binaries, WebDriver compatibility, network permission, and user approval to access target sites.
- OCR tasks: require PaddleOCR or another OCR engine plus image files at the referenced paths.
- Image background removal: require `rembg` and image processing dependencies.
- Game generation: require `pyxel` and clarify whether code may create windows or write files.

## Planning and Execution Loop

Classic `DataInterpreter` in `plan_and_act` mode:

1. Builds or updates a plan from the user requirement.
2. For each task, prepares plan status and optional tool information.
3. For data-preprocess/feature-engineering/model-train tasks, may run a data-check code block based on finished task code.
4. Asks `WriteAnalysisCode` to generate Python.
5. Executes the code through `ExecuteNbCode` in a notebook kernel.
6. Records code/output in working memory and retries up to three times; reflection is used only after the first failed attempt when enabled.
7. Terminates the notebook kernel after `plan_and_act` completes or raises.

Implications:

- Generated code is stateful across cells in the same `ExecuteNbCode` instance.
- A failure can still leave files, variables, or partial outputs in the workspace.
- `use_reflection=True` can improve debugging but increases LLM calls and cost.
- `auto_run=False` is useful when a human should approve plan steps before execution.

## Notebook and Code Execution Caveats

`ExecuteNbCode` creates a notebook, starts a kernel on first execution, and writes `code.ipynb` under the configured MetaGPT workspace. It supports `language="python"` and `language="markdown"`.

Important behavior:

- Default execution timeout is `600` seconds; use `ExecuteNbCode(timeout=...)` for bounded diagnostics.
- `CellTimeoutError` interrupts the kernel and returns a timeout message.
- `DeadKernelError` triggers a reset path.
- `!pip` output is truncated and treated as unsuccessful to discourage package installation inside generated notebooks.
- `git clone` output is truncated but may still perform network/file side effects if executed.
- Plot outputs may attempt to show images when not in IPython; prefer noninteractive backends in headless environments.
- Always call `await executor.terminate()` after direct executor tests.

Direct executor diagnostic example:

```python
import asyncio
from metagpt.actions.di.execute_nb_code import ExecuteNbCode

async def main():
    executor = ExecuteNbCode(timeout=5)
    try:
        output, ok = await executor.run("print('hello world')")
        print(ok, output)
    finally:
        await executor.terminate()

asyncio.run(main())
```

## RoleZero and DataAnalyst Workflows

`RoleZero` is a dynamic react role. It plans, selects commands, and executes registered tools such as plan operations, browser actions, editor actions, terminal commands, and human questions. `DataAnalyst` subclasses it for data-heavy tasks and exposes `DataAnalyst.write_and_exec_code` as a registered tool.

Use `DataAnalyst` when the agent needs a richer dynamic loop with browser/search/editor plus notebook code execution:

```python
from metagpt.roles.di.data_analyst import DataAnalyst

analyst = DataAnalyst()
await analyst.run("Analyze this CSV and summarize trends; ask before writing files.")
```

Notes:

- `DataAnalyst.tools` includes `Plan`, `DataAnalyst`, `RoleZero`, `Browser`, limited `Editor`, and `SearchEnhancedQA`.
- `custom_tools` defaults include web scraping, `Terminal`, and limited editor operations for code-writing context.
- `write_and_exec_code()` returns `No current_task found...` unless a plan current task exists.
- Successful generated code updates the current task result; failed code returns a failure status and captured error.

## SWEAgent, Engineer2, and TeamLeader

Use these DI-adjacent roles only when the request explicitly asks for dynamic issue fixing, engineering, or team leadership behavior:

- `SWEAgent` uses `Bash`, browser navigation, `RoleZero`, and `git_create_pull`; it is designed for resolving GitHub issues or bugs in a repository.
- `Engineer2` uses `Plan`, `Editor`, terminal commands, browser, search QA, code review, image getter, deployer, and optional eval behavior; it can write files and deploy artifacts.
- `TeamLeader` manages role communication, has a short max react loop, and publishes messages to named team members.

These roles can modify files, run commands, access network resources, and attempt submission/deployment flows. Require an isolated workspace and explicit approval before running them on user repositories.

## Tool Usage Prerequisites

DI tool lists are names looked up in MetaGPT's tool registry/recommenders. Examples include:

- `tools=["Browser"]` for browser workflows in `react` mode.
- `tools=["Terminal", "Editor"]` for codebase issue fixing with explicit one-step-at-a-time prompts.
- `tools=["magic_function"]` after registering a custom function with `@register_tool()`.
- `tools=["<all>"]` to let the recommender consider all registered tools; this is broad and should be opt-in.
- `tool_recommender=TypeMatchToolRecommender(tools=["<all>"])` for benchmark-style tool matching.

For tool registry/search/browser/editor/data-preprocess internals, route to `rag-and-tools`; this sub-skill covers workflow-level use and safety.

## Safe Adaptation Checklist

Before running a DI workflow:

- Confirm LLM provider credentials are configured and not placeholder values.
- Confirm generated code may run and identify the sandbox/workspace.
- Validate every data path exists or create a corrected data layout.
- Strip secrets from prompts, code, notebooks, logs, and saved history.
- Ask before network access, browser automation, email sending, package installation, `git clone`, repository edits, or deployment.
- Bound long tasks with smaller samples, shorter timeouts, or a planning-only dry run.
- Keep benchmark/DABench work optional because it requires downloads and expensive LLM/code execution.
