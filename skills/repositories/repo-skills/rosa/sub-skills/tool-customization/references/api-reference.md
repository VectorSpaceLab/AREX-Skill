# Tool customization API reference

These facts are from ROSA `v1.0.10` / `jpl-rosa==1.0.10`, the checked-in
package implementations, selected native tests, and the sanitized installed
API inspection. They describe the public shape; they do not make a ROS
middleware installation available.

## `ROSATools`

The constructor is:

```python
ROSATools(ros_version: Literal[1, 2], blacklist: Optional[List[str]] = None)
```

Construction proceeds in this order:

1. Create an empty private tool list and retain the selected version and
   blacklist.
2. Import and scan the base `calculation`, `log`, and `system` modules.
3. Import and scan **only** `ros1` when `ros_version == 1`, or **only** `ros2`
   when `ros_version == 2`.
4. Raise `ValueError("Invalid ROS version. Must be either 1 or 2.")` for any
   other value, after the base-module imports.

The family import is therefore lazy with respect to the unselected family,
but not optional during `ROSATools` construction. A direct import and
inspection of the three base modules is a useful middleware-free smoke test;
constructing the full collection still needs the selected ROS family's Python
modules (and, for ROS 2, the CLI/runtime used by its tools).

`get_tools() -> List[Tool]` returns the internal list. It is a live list, not a
copy; callers can observe or mutate it. Every accepted object must have both
`name` and `func` attributes. There is no duplicate-name check and no explicit
warning for rejected plain functions or unrelated module attributes.

### Adding individual tools

```python
rosa_tools.add_tools(tools: list) -> None
```

Each item is passed to the same private acceptance path. Use LangChain's
`@tool` decorator (or an equivalent tool object with valid metadata and a
callable `func`) so the agent receives a name, description, and argument
schema. `add_tools` appends to the existing default/family tools; it does not
replace them or deduplicate them. Passing the same object twice can expose it
twice.

### Adding packages

```python
rosa_tools.add_packages(
    tool_packages: List,
    blacklist: Optional[List[str]] = None,
) -> None
```

Each package/module is scanned with `dir(package)`. Public attributes (names
not starting with `_`) are read and accepted when they have `name` and `func`.
The `blacklist` parameter is present in the signature, but in `v1.0.10` it is
passed to an iterative helper that does not use that argument. Effective
injection is driven by the blacklist retained when the `ROSATools` object was
constructed. In the normal `ROSA` path, pass the blacklist to `ROSA(...)` so
that constructor-time scanning and later package additions share the intended
value; do not assume `add_packages(..., blacklist=...)` alone changes existing
state.

`ROSA` hands off customization as follows:

```python
ROSA(
    ros_version,
    llm,
    tools=custom_tools,
    tool_packages=custom_packages,
    prompts=robot_prompts,
    blacklist=default_blacklist,
    ...,
)
```

Its constructor calls `_get_tools`, which creates `ROSATools(ros_version,
blacklist=blacklist)`, then calls `add_tools(tools)` and
`add_packages(packages, blacklist=blacklist)` when supplied. The rest of the
constructor builds the tool-calling agent and executor from that collection.
Use [agent-core](../../agent-core/SKILL.md) for the complete `ROSA`
constructor, model, streaming, and executor contract.

## `inject_blacklist`

The helper has the shape:

```python
inject_blacklist(default_blacklist: List[str]) -> decorator
```

ROSA applies it to an accepted tool only when the retained blacklist is
truthy **and** `tool.func.__code__.co_varnames` contains `"blacklist"`.
Therefore:

- A tool without a `blacklist` parameter is not modified.
- The tool function must visibly expose the parameter in its code variables;
  hiding it behind an unrelated adapter can prevent injection.
- A call with a first positional dictionary mutates that dictionary in place.
  If it contains `blacklist`, the effective value becomes
  `default_blacklist + caller_blacklist`; otherwise it becomes the default.
- A keyword `blacklist` is likewise replaced by
  `default_blacklist + caller_blacklist`; if omitted and the wrapped function
  declares it, the default is inserted.
- Concatenation preserves order and does not deduplicate. A caller can see
  repeated names.
- `functools.wraps` preserves metadata and a rebuilt signature preserves the
  parameter list while replacing the `blacklist` default with the default
  list. Treat that list as configuration, not as mutable per-call state.

The helper injects a value; it does not itself filter tool names or guarantee
that a custom function honors the value. ROS-family tools use the parameter
to filter relevant results. A custom tool should document exactly what its
blacklist means, or omit the parameter rather than pretending to support
filtering.

Because wrapping assigns a new function to `tool.func`, adding a blacklisted
tool can alter the supplied tool object. Use fresh tool objects when testing
multiple blacklist configurations.

## `RobotSystemPrompts`

Constructor:

```python
RobotSystemPrompts(
    embodiment_and_persona: Optional[str] = None,
    about_your_operators: Optional[str] = None,
    critical_instructions: Optional[str] = None,
    constraints_and_guardrails: Optional[str] = None,
    about_your_environment: Optional[str] = None,
    about_your_capabilities: Optional[str] = None,
    nuance_and_assumptions: Optional[str] = None,
    mission_and_objectives: Optional[str] = None,
    environment_variables: Optional[dict] = None,
)
```

The first argument is stored as `embodiment`; the other string fields retain
their descriptive names. `environment_variables` is stored but is not a
string attribute, so `__str__` does not serialize its dictionary. It should
not be used as a secret store.

`as_message() -> tuple` returns `("system", str(prompts))`. The string begins
and ends with ROSA's robot-specific prompt delimiters and includes each
non-empty, non-whitespace string attribute. Labels are generated from
attribute names and title-cased. Empty fields are omitted. Because iteration
uses `dir(self)`, rendered field order follows the object's attribute
ordering (normally alphabetical), not necessarily constructor argument order.

Pass a **new** prompt object through `ROSA(prompts=...)`. In v1.0.10,
`ROSA._get_prompts` aliases the module-level `system_prompts` list and calls
`.append()` when custom prompts are supplied. That means constructing an
agent with custom prompts can persist the custom message in later agents in
the same process. Do not edit `system_prompts` as a customization mechanism;
see [workflows.md](workflows.md) and the prompt-mutation troubleshooting note.
