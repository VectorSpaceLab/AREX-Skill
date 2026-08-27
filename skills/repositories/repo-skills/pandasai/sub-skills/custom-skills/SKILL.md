---
name: custom-skills
description: "Guides PandasAI custom function skills, @pai.skill decorators,
  SkillType validation, global registry management, and skill-related
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Custom Skills

Use this sub-skill when a user wants PandasAI to make custom Python functions
available to generated analysis code through `@pai.skill()` or the
`pandasai.ee.skills` registry.

PandasAI custom skills are runtime functions for PandasAI-generated code. They
are not DisCo Agent Skills and are not `SKILL.md` directories.

## Fast route

1. Define a normal Python function with type hints and a useful docstring.
2. Decorate it with `@pai.skill()` or `@pai.skill("custom_name")`.
3. Configure the LLM and run PandasAI chat as usual.
4. If testing registry behavior, clear `SkillsManager` between tests to avoid
   duplicate-name leakage.
5. If the task is about using those functions during chat, route back to
   [`../conversational-analysis/SKILL.md`](../conversational-analysis/SKILL.md)
   after registration is correct.

```python
import pandasai as pai

@pai.skill()
def format_currency(amount: float) -> str:
    """Format a numeric amount as US dollars."""
    return f"${amount:,.2f}"
```

## Read next

- [`references/api-reference.md`](references/api-reference.md) for `SkillType`,
  decorator forms, and `SkillsManager` methods.
- [`references/workflows.md`](references/workflows.md) for defining, naming,
  testing, and clearing custom skills.
- [`references/troubleshooting.md`](references/troubleshooting.md) for missing
  docstrings, duplicate registry names, lambda functions, and terminology
  confusion.
- [`scripts/skill_registry_smoke.py`](scripts/skill_registry_smoke.py) for a
  no-LLM registry behavior smoke.

## Boundaries

- Route dataframe chat, generated-code response handling, and LLM configuration
  to [`../conversational-analysis/SKILL.md`](../conversational-analysis/SKILL.md).
- Route sandbox/security choices to
  [`../sandbox-and-security/SKILL.md`](../sandbox-and-security/SKILL.md).
- Do not create or modify DisCo repo-skill files when the user asks about
  PandasAI `@pai.skill`; these are unrelated skill systems.

## Enterprise note

PandasAI documentation marks custom skills as an Enterprise feature for
production use. For local experimentation and tests, the decorator and registry
exist in the package. For production deployments, warn the user to confirm their
PandasAI license/plan.

## Safe validation

```bash
python sub-skills/custom-skills/scripts/skill_registry_smoke.py
```

The helper registers a small skill, verifies duplicate-name protection, verifies
no-docstring failure behavior, and prints JSON. It does not need a real LLM or
provider key.

## Common gotchas

- A function must have a docstring unless `SkillType(..., description=...)` is
  used directly.
- Duplicate skill names in the global registry raise `ValueError`.
- Decorated functions are replaced by `SkillType` objects, but remain callable.
- Registry state is global; clear it in tests before registering predictable
  names.
- Lambdas need an explicit name and description when wrapped directly.
