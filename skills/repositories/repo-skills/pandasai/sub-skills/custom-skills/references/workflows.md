# Custom Skills Workflows

## Define and register a skill

```python
import pandasai as pai

@pai.skill()
def calculate_bonus(salary: float, performance: float) -> float:
    """Calculate a bonus amount from salary and performance."""
    if performance >= 90:
        return salary * 0.15
    if performance >= 70:
        return salary * 0.10
    return salary * 0.05
```

The decorated function becomes a `SkillType` object and is registered globally.
Any subsequent `Agent` created in the same process can see it.

## Give a custom name

```python
import pandasai as pai

@pai.skill("format_currency")
def money(amount: float) -> str:
    """Format currency."""
    return f"${amount:,.2f}"
```

Use a custom name when the function name is not the best name for generated code.

## Clear and rebuild the registry for tests

```python
from pandasai.ee.skills.manager import SkillsManager

SkillsManager.clear_skills()
# register a few skills
# ...
SkillsManager.clear_skills()
```

Clear the registry before each isolated test if you want predictable duplicate
checking.

## Verify registry behavior

Use the bundled smoke helper:

```bash
python sub-skills/custom-skills/scripts/skill_registry_smoke.py
```

That helper checks the happy path, duplicate-name protection, and missing
docstring behavior without requiring an LLM or network access.

## Use skills inside chat

Once registered, custom skills are available to PandasAI-generated code inside
`Agent` conversations. After registration, route to the conversational-analysis
sub-skill for the chat workflow itself.

```python
import pandasai as pai
from pandasai.llm.fake import FakeLLM

pai.config.set({"llm": FakeLLM("result = {'type': 'string', 'value': format_currency(125)}")})
```

The skill function must already be registered in the process before the agent is
created.
