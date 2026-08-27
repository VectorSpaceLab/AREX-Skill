# Software Company Workflows

This reference distills MetaGPT's core virtual software-company usage. Commands that generate projects or call `Team.run(...)` contact an LLM provider and may spend API budget; mark them as prerequisites/skips in smoke tests unless the user has confirmed a working `config2.yaml` and budget.

## Configuration Workflow

MetaGPT reads `config2.yaml` from these locations, with user config taking precedence:

1. `~/.metagpt/config2.yaml`
2. `config/config2.yaml` in a source checkout

Initialize user config:

```bash
metagpt --init-config
```

Then edit `~/.metagpt/config2.yaml` and replace placeholder values. The minimal LLM block is:

```yaml
llm:
  api_type: "openai"
  model: "gpt-4-turbo"
  base_url: "https://api.openai.com/v1"
  api_key: "YOUR_REAL_API_KEY"
```

Provider notes:

- OpenAI-style providers need `base_url` ending in `/v1` unless the provider documents a different path.
- Azure, Ollama, Groq, reverse proxies, and Claude-through-compatible-proxy setups use the same config file but provider-specific `api_type`, `model`, `base_url`, and authentication fields.
- Do not run project generation while `api_key` is still `YOUR_API_KEY`; `Config.default()` / package import paths may fail validation or later provider calls.
- If both config files exist, a stale placeholder in `~/.metagpt/config2.yaml` overrides a fixed repo-local config.

## CLI Project Generation

Basic startup:

```bash
metagpt "Create a 2048 game"
```

Common variants:

```bash
metagpt "Write a cli snake game" --no-implement
metagpt "Write a cli snake game" --code-review
metagpt "Write a cli snake game" --run-tests --n-round 8
metagpt "Write a cli snake game based on pygame" --project-name snake_pygame
```

CLI behavior:

- The `idea` positional argument is the one-line product requirement.
- Project outputs are created in the configured workspace, commonly `workspace/<project-name>/` for source checkouts or the package's configured workspace.
- Generated outputs can include requirement documents, competitive analysis, PRD, system design, task/API docs, code, tests, summaries, and rendered diagram resources when rendering dependencies are available.
- `--investment` sets the maximum dollar budget stored on the team's cost manager.
- `--n-round` bounds the number of team simulation rounds.
- `--code-review/--no-code-review`, `--run-tests/--no-run-tests`, and `--implement/--no-implement` are Typer boolean pairs; use the exact dashed spellings exposed by `metagpt --help`.
- `--max-auto-summarize-code -1` allows unlimited automatic `SummarizeCode` actions; `0` disables automatic repeats and is the default.

Do not use project-generation commands as normal smoke tests. They invoke roles such as `TeamLeader`, `ProductManager`, `Architect`, `Engineer2`, and `DataAnalyst`, then run `Team.run(...)` against an LLM-backed environment.

## Python Project Generation

Minimal Python usage:

```python
from metagpt.software_company import generate_repo
from metagpt.utils.project_repo import ProjectRepo

project_path = generate_repo(
    "Create a 2048 game",
    investment=3.0,
    n_round=5,
    code_review=True,
    run_tests=False,
    implement=True,
    project_name="game_2048",
)
repo = ProjectRepo(project_path)
print(repo)
```

`generate_repo(...)` returns the configured project path from the active context. It imports config, constructs a `Context`, hires the default software-company roles when not recovering, invests budget, runs `company.run(n_round=n_round, idea=idea)`, and returns `ctx.kwargs.get("project_path")`.

## Incremental Project Updates

Use incremental mode when the user wants MetaGPT to modify or continue an existing generated project:

```bash
metagpt "Add keyboard controls and a pause menu" --inc --project-name game_2048
metagpt "Add keyboard controls and a pause menu" --inc --project-path workspace/game_2048
```

Rules of thumb:

- `--inc` needs project context. Supply either `--project-name` for a project in the configured workspace or `--project-path` for a concrete existing project directory.
- `--reqa-file` points to a source file for rewriting QA code during incremental QA workflows.
- Keep `--project-name` unique for new projects to avoid confusing existing workspace directories.
- If MetaGPT cannot locate the old project, check workspace configuration, spelling, and whether `project_path` points at the project root rather than an inner source file.

## Serialized-Team Recovery

Use recovery when a prior team state was serialized and the user wants to continue from that exact state:

```bash
metagpt "ignored when recovering" --recover-path workspace/storage/team
```

Python equivalent:

```python
from metagpt.software_company import generate_repo

project_path = generate_repo(
    idea="Continue from saved team state",
    recover_path="workspace/storage/team",
    n_round=3,
)
```

Important behavior:

- `recover_path` must exist and its string path must end with `team`.
- The directory must contain `team.json`; otherwise `Team.deserialize(...)` raises a recovery metadata error.
- When recovery succeeds, `generate_repo(...)` replaces the supplied `idea` with `company.idea` from the serialized team.
- Recovery continues through `company.invest(...)` and `company.run(...)`, so it still needs valid LLM config and budget.

## Project Outputs

Generated project paths are represented by `ProjectRepo`. Useful locations include:

| Area | Purpose |
| --- | --- |
| project root | Git/File repository wrapper root for generated code and docs |
| docs repositories | PRD, system design, tasks, code summaries, graph/class views, and code plan/change files |
| resources repositories | rendered PDFs/images and visual artifacts for PRD, design, tasks, graphs, and summaries |
| tests repository | generated test code |
| test outputs repository | generated test execution outputs |
| source path | discovered by `get_project_srcs_path(...)`; call `ProjectRepo(...).with_src_path(path)` before using `.srcs` manually |

`str(ProjectRepo(path))` prints a compact summary of the project workdir, docs files, and source files when source files exist.

## Custom Action, Role, and Team Patterns

Core pattern for a custom action:

```python
from metagpt.actions import Action

class SimpleWriteCode(Action):
    name: str = "SimpleWriteCode"

    async def run(self, instruction: str):
        prompt = f"Write code for: {instruction}"
        return await self._aask(prompt)
```

Core pattern for a role with one action:

```python
from metagpt.roles.role import Role
from metagpt.schema import Message

class SimpleCoder(Role):
    name: str = "Alice"
    profile: str = "SimpleCoder"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([SimpleWriteCode])

    async def _act(self) -> Message:
        todo = self.rc.todo
        latest = self.get_memories(k=1)[0]
        content = await todo.run(latest.content)
        return Message(content=content, role=self.profile, cause_by=type(todo))
```

Core pattern for multi-action order:

```python
from metagpt.roles.role import RoleReactMode

self.set_actions([SimpleWriteCode, SimpleRunCode])
self._set_react_mode(react_mode=RoleReactMode.BY_ORDER.value)
```

Core pattern for a multi-role team:

```python
from metagpt.actions import UserRequirement
from metagpt.team import Team

team = Team()
team.hire([SimpleCoder(), SimpleTester(), SimpleReviewer()])
team.invest(investment=3.0)
team.run_project("write a function that calculates the product of a list")
await team.run(n_round=5)
```

Message-routing notes:

- Roles call `self._watch([ActionClass])` to select messages caused by specific actions.
- Default roles watch `UserRequirement` unless `observe_all_msg_from_buffer` is enabled or custom watch settings are provided.
- `Message(content=..., role=..., cause_by=type(todo))` is the common return shape for custom `_act(...)` methods.
- Debate-style roles can set `sent_from` and `send_to` to route between named roles.

Examples such as debate agents, game code generation, and custom coder/tester/reviewer teams are reference patterns only; they call `_aask(...)` or run `Team.run(...)` and therefore require real provider config and spend.

## No-LLM Dry Validation

Safe checks that should not call an LLM:

```bash
python sub-skills/software-company/scripts/inspect_role_action.py --help
python sub-skills/software-company/scripts/inspect_role_action.py --json
python sub-skills/software-company/scripts/inspect_role_action.py --check-cli-help --json
metagpt --help
```

What these checks prove:

- `metagpt.software_company.generate_repo` and `startup` signatures are importable.
- `Action`, `Role`, `RoleReactMode`, `Message`, `Team`, and `ProjectRepo` core APIs are importable.
- The `metagpt` console entry point is discoverable or CLI help can execute.
- A simple local custom class shape can be inspected without `_aask(...)`, `Team.run(...)`, API keys, browsers, downloads, or workspace writes.

What these checks do not prove:

- Provider authentication works.
- A project can be generated successfully.
- Mermaid/browser rendering works.
- Long project outputs fit within the selected model context.
