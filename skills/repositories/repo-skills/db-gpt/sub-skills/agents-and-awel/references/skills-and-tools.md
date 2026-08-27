# Skills, tools, resources, and middleware

DB-GPT models tools and many agent capabilities as `Resource` objects. A tool is not
called by merely appearing in a prompt: an action (usually `ToolAction`) must parse the
model output and execute a named tool from a bound `ToolPack` or resource pack.

## Define and validate a tool

The shortest reliable form is a documented, typed function:

```python
from dbgpt.agent.resource import ToolPack, tool

@tool
def add(left: int, right: int) -> int:
    """Add two integers and return the sum."""
    return left + right

tools = ToolPack([add])
```

`@tool` returns a wrapper that retains the `FunctionTool` at `function._tool` and marks
the wrapper with DB-GPT's tool identifier. The `FunctionTool` constructor is:

```text
FunctionTool(
    name,
    func,
    description=None,
    args=None,
    args_schema=None,
    parse_execute_args_func=None,
)
```

Rules that prevent ambiguous model schemas:

- A function needs a docstring unless an explicit non-empty `description` is supplied.
- Inferred arguments use Python annotations and defaults. A parameter without a Python
  default is required; a parameter with a default is optional.
- `args` may be a mapping of `ToolParameter` instances or mappings containing `type`,
  optional `title`, `description`, `required`, and `default`. Do not mix the two forms.
- `args_schema` may be a pydantic `BaseModel` class and is useful when the model input
  contract is richer than a function signature. Ensure every schema field actually
  matches what the function can accept; schema generation does not execute the function.
- `ToolParameter.type` is the provider-facing schema string (`string`, `integer`,
  `number`, `array`, `object`, etc.). `ToolParameter` fills a missing title from the
  parameter name and a missing description from the title.
- A sync function must use `execute`; an async function must use `async_execute`.
  Calling the wrong one raises `ValueError`. `ToolPack.async_execute` can invoke either
  kind, while `ToolPack.execute` rejects async tools.

Inspect before binding:

```python
ft = add._tool
assert ft.name == "add"
assert set(ft.args) == {"left", "right"}
text, _ = await ft.get_prompt(prompt_type="openai")
```

`get_prompt(prompt_type="openai")` emits an object schema with `properties` and a
`required` list. The default prompt emits a list of parameter descriptions. Do not
hand-edit a provider schema while retaining a conflicting `args_schema`.

`ToolPack(resources, name="Tool Resource Pack", **kwargs)` accepts tool instances,
`@tool` functions, lists, or compatible resource packs. Its pack lookup is by exact
tool name. It filters unknown keyword arguments before execution; this is convenient
for compatibility but can hide a model typo, so validate the model-produced argument
keys before invoking a high-risk tool. Missing tools raise a tool-not-found error and
execution failures are wrapped in `ToolExecutionException`.

`ToolPack.parse_execute_args(resource_name, input_str)` delegates to the selected tool.
The default JSON parser accepts an object and turns an empty list into `{}`. A custom
parser can return `(positional_args, keyword_args)` or raise an actionable
`ValueError`. Never use `eval` to parse model arguments.

## Actions and resources

Import resource types from `dbgpt.agent.resource` and bind a pack before build:

```python
from dbgpt.agent.expand.actions.tool_action import ToolAction

agent.bind(tools)
agent.bind(ToolAction)
```

`ToolAction` declares `resource_need == ResourceType.Tool` and expects model output
that parses into a `ToolInput` with `tool_name`, `args`, and `thought`. The agent's
availability check therefore fails if the action is present but no tool resource is
bound. A skill's `required_tools` list is descriptive metadata; it does not auto-create
or auto-bind those tools.

Other resources use the same `Resource` contract (`type()`, `name`, `get_prompt()`,
optional `preload_resource()`, `execute()`/`async_execute()`). `ResourceType` includes
`DB`, `Knowledge`, `Tool`, `Skill`, `AWELFlow`, `App`, and file/pack/connector types.
A `ResourcePack` can contain sub-resources; `Resource.from_resource()` and
`get_resource_by_type()` are the normal typed lookup boundary. Avoid passing raw
objects that are not `Resource` instances into `bind()`.

## Programmatic core skills

The core skill exports are:

```python
from dbgpt.agent.skill import (
    Skill,
    SkillBuilder,
    SkillLoader,
    SkillManager,
    SkillMetadata,
    SkillParameters,
    SkillType,
    get_skill_manager,
    initialize_skill,
)
```

`SkillMetadata(name, description, version="1.0.0", author=None,
skill_type=SkillType.Custom, tags=[])` describes the skill. `Skill(...)` adds an
optional `PromptTemplate`, `required_tools`, `required_knowledge`, `actions`, and
arbitrary `config`.

`SkillBuilder(name, description)` supports fluent methods:

```python
skill = (
    SkillBuilder("local-math", "Use local arithmetic tools for math requests")
    .with_version("1.0.0")
    .with_skill_type(SkillType.Chat)
    .with_tags(["math", "local"])
    .with_prompt_template("Use only the supplied arithmetic capability.")
    .with_required_tool("add")
    .build()
)
```

`with_skill_type` accepts a `SkillType` or a valid enum string (`coding`,
`data_analysis`, `web_search`, `knowledge_qa`, `chat`, or `custom`). Build-time
validation is intentionally light; validate referenced tool and knowledge names
against the resources that will be bound.

Initialize and register manually when an application owns the registry:

```python
from dbgpt.component import SystemApp

system_app = SystemApp()
initialize_skill(system_app)
manager = get_skill_manager(system_app)
manager.register_skill(skill_instance=skill, name="local-math")
selected = manager.get_skill(name="local-math", version="1.0.0")
```

`SkillManager.register_skill` accepts either a class or an instance. Duplicate class
keys raise unless `ignore_duplicate=True`. `get_skill` can filter by exact name,
`SkillType`, and version; missing results are `None`. `list_skills()` returns metadata
dictionaries. `build_skill_from_parameters()` currently resolves by `skill_name`; do
not assume all fields of `SkillParameters` (version/config/load flags) enforce
selection or dependency loading. `initialize_skill()` installs the manager in a
`SystemApp`; `get_skill_manager()` can create a default app when no app is supplied,
but explicit app ownership is easier to test.

Bind a selected core skill before building an agent. `ConversableAgent.bind(skill)`
sets the agent's private skill and adopts its prompt template as `bind_prompt`; it does
not verify `required_tools` or load a knowledge resource. Perform that check in a
skill-aware application layer.

## File-based skills and registration

There are two related file workflows; do not conflate them:

### `SkillLoader`

`SkillLoader(skill_dirs=None)` can load a JSON/YAML file, a Claude-style `SKILL.md`, a
Python module, or all supported files in a directory:

```python
loader = SkillLoader()
core_skill = loader.load_skill_from_file("./skills/local-math/SKILL.md")
module_skill = loader.load_skill_from_module("my_skills.local_math")
all_skills = loader.load_skills_from_directory("./skills", recursive=True)
```

A `SKILL.md` must start with frontmatter and include `name` and `description`:

```markdown
---
name: local-math
description: Use local arithmetic tools for math requests.
version: 1.0.0
skill_type: chat
required_tools:
  - add
---

Use the supplied tool and report the exact result.
```

The file loader converts the Claude-style parser result into a core `Skill`, including
its instructions as a prompt and its declared required tool/knowledge lists. For
JSON/YAML, the current loader builds core metadata and config; do not assume arbitrary
`prompt_template`, `required_tools`, or `actions` keys in those files are hydrated
unless you verify that behavior in the installed version. Prefer `SkillBuilder` or a
`SKILL.md` fixture for a complete prompt/dependency contract.

`load_skill_from_module` imports the module and looks for a `Skill` class subclassing
`SkillBase`, then instantiates it without arguments. Keep such classes constructible
without credentials or network access.

### Progressive-disclosure middleware

`SkillsMiddleware(sources=[...])` scans each immediate child directory for `SKILL.md`.
It initially stores metadata and reads complete content lazily through
`LoadedSkill.content`; `get_prompt_template()` turns that content into a
`PromptTemplate`. Source order matters: later source directories override earlier
skills with the same name. `SkillsMiddlewareV2` adapts this behavior to
`AgentMiddleware`; it can auto-load, keyword-match, and inject a skills section into the
system prompt.

The middleware frontmatter parser requires `name` and `description`, limits a skill
file to 10 MiB, and recognizes optional `version`, `author`, `skill_type`, `tags`, and
`allowed-tools`. Names are expected to be lowercase alphanumeric words separated by
single hyphens (maximum 64 characters); invalid names are logged as warnings, so a
caller should reject them before publication. A string `allowed-tools` is split into
names for metadata; do not mistake that field for an authorization boundary.

`match_skills(user_input)` uses keywords extracted from the description and returns all
matching skills. Matching is substring/keyword based and can produce false positives;
explicitly choose `get_skill(name)` or `set_skill(name)` for safety-critical workflows.
`SkillsAgent` and `MiddlewareAgent` provide convenience integration, but constructing
one does not supply an LLM client or make a tool safe.

### Skill file safety

Skill instructions are prompt content, not a sandbox. A skill may also describe scripts,
but `SkillManager.execute_script`/script-file helpers can invoke the code server and
write files. Do not execute a skill-provided script while merely validating metadata.
Require an explicit trusted-workspace policy, inspect code, pass bounded arguments, and
honor the personal-skill execution disable setting when the host uses one. Never put
secrets or private absolute paths in a published skill.

## Optional MCP tools

`MCPToolPack` can wrap one or more remote MCP SSE/HTTP servers. Its constructor accepts
server URLs, headers, TLS verification settings, transport, and overwrite behavior;
creating or preloading it may perform a network handshake and discover remote tools.
Treat MCP as optional and blocked in a no-network verification environment.

When `ConnectorManager` owns MCP packs, routed names are prefixed as
`mcp__<prefix>__<original_name>`. Built-in single instances use the connector type;
multiple instances add a slug; custom connector types use the display-name slug.
Skills can request connector types, but the connector integration warns and returns an
empty set when a required connector is absent rather than necessarily blocking. Verify
availability before presenting a skill as runnable.

## Malformed dependency checklist

For a required tool that is missing or malformed:

1. Parse the skill metadata and normalize `required_tools` to a list of exact names.
2. Look up the corresponding tools in the bound `ResourceType.Tool` pack.
3. For each tool, verify non-empty description, unique name, valid argument mapping,
   and a matching sync/async execution path.
4. Compare every required model argument with `tool.args`; reject missing required
   fields and unexpected high-risk fields instead of relying on `ToolPack`'s filtering.
5. Return an actionable error naming the skill, missing/invalid tool, and remediation
   (register/bind the tool or remove the dependency). Do not silently downgrade the
   skill to a prompt-only agent.
6. If the skill is only metadata-loaded by middleware, keep it inactive until this
   dependency check succeeds.
