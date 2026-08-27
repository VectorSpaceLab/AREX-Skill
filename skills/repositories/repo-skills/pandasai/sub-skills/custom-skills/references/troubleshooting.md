# Custom Skills Troubleshooting

## Missing docstring

**Symptom**: `ValueError: Function must have a docstring if no description is provided`.

**Cause**: `SkillType` was created from a callable without a docstring and without
an explicit `description`.

**Fix**: Add a docstring or pass `description=` when constructing the skill.

## Duplicate name

**Symptom**: `ValueError: Skill with name '...' already exists.`

**Cause**: The global registry already contains a skill with that name.

**Fix**: Choose a new skill name or call `SkillsManager.clear_skills()` in test
setup before registering a new set of skills.

## Lambda or anonymous callable

**Symptom**: The callable is difficult to name or inspect.

**Cause**: Lambda functions do not have a useful docstring or stable name by
default.

**Fix**: Wrap the lambda in a named function, or construct `SkillType` with an
explicit `name` and `description`.

## Decorator returned a different object

**Symptom**: A decorated function is no longer a plain function.

**Cause**: `@pai.skill()` returns a `SkillType` wrapper.

**Fix**: This is expected. Call the object normally, but treat it as a registry-
backed skill when building prompts or tests.

## Registry state leaked across tests

**Symptom**: Tests fail only when run after other tests.

**Cause**: `SkillsManager` is global process state.

**Fix**: Clear the registry before and after tests that register skills.

## Confusing PandasAI skills with DisCo skills

**Symptom**: The user asks for a `@pai.skill` function but the response talks about
creating a Markdown skill file.

**Cause**: The two systems share the word "skill" but are unrelated.

**Fix**: Explain that PandasAI skills are runtime Python callables registered in
process, while DisCo skills are repo skill directories used by the agent.

## Enterprise note confusion

**Symptom**: The user expects custom skills to be free-only or fully enterprise-
locked.

**Fix**: Clarify that the package exposes the decorator and registry for local use,
but the documentation marks production custom skills as an Enterprise feature.
