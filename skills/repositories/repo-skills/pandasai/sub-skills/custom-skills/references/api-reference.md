# PandasAI Custom Skills API Reference

## Purpose

Use this for verified custom-skill decorator, `SkillType`, and `SkillsManager`
behavior. Workflow recipes are in `workflows.md`.

## Decorator forms

```python
import pandasai as pai

@pai.skill
def implicit_no_parentheses(x: int) -> int:
    """Return x unchanged."""
    return x

@pai.skill()
def default_name(x: int) -> int:
    """Return x unchanged."""
    return x

@pai.skill("custom_name")
def original_name(x: int) -> int:
    """Return x unchanged."""
    return x
```

All forms create a `SkillType` object and add it to the global
`SkillsManager` registry.

## `SkillType`

`SkillType` stores:

| Attribute | Meaning |
| --- | --- |
| `func` | Original callable |
| `name` | Skill name, defaulting to `func.__name__` unless custom name is supplied |
| `description` | Explicit description or function docstring |
| `_signature` | String such as `def function_with_params(x: int, y: int = 5) -> int:` |

Important behavior:

- The callable must have a docstring if no description is provided.
- A lambda wrapped directly needs an explicit `name` and `description` to be
  useful and valid.
- `SkillType.__call__` calls the underlying function.
- `SkillType.stringify()` returns the source text for the original function
  when inspectable.
- `str(skill)` emits a function-like block with signature and docstring; this is
  what agent prompts can include.

## `SkillsManager`

The registry is global process state.

| Method | Behavior |
| --- | --- |
| `add_skills(*skills)` | Adds one or more `SkillType` objects; duplicate names raise `ValueError`. |
| `skill_exists(name)` | Returns true when a skill name is registered. |
| `has_skills()` | Returns true when registry is non-empty. |
| `get_skill_by_func_name(name)` | Returns the matching skill object or `None`. |
| `get_skills()` | Returns a copy of the registered skills list. |
| `clear_skills()` | Clears the global registry. Use in tests and isolated examples. |

`AgentState.initialize(...)` copies `SkillsManager.get_skills()` into the agent
state, so register skills before creating the agent or starting a chat when you
need those functions available.

## Naming rules

Use names that are valid Python function identifiers because generated code will
call the function by name. Prefer specific names such as `format_currency` or
`calculate_bonus` instead of generic names such as `helper`.

## Not the same as DisCo skills

PandasAI skills are Python callables registered in a process. DisCo Agent Skills
are Markdown/runtime operating graphs. Do not solve a PandasAI `@pai.skill()`
request by creating a `SKILL.md` file.
