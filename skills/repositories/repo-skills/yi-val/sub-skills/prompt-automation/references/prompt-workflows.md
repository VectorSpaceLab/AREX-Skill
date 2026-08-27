# Prompt automation workflows

## Auto prompt generation for a custom task

1. Define the target custom function and its input parameters.
2. Configure `openai_prompt_data_generator.input_function.parameters` to match those parameters.
3. Configure `openai_prompt_based_variation_generator.variables` so generated prompts preserve placeholders used by the custom function.
4. In the custom function, wrap the prompt:

```python
prompt = str(
    StringWrapper(
        template="Generate landing page headline for {tech_startup_business}",
        variables={"tech_startup_business": tech_startup_business},
        name="task",
        state=state,
    )
)
```

5. Add evaluators and a selection strategy in the evaluation-optimization sub-skill.
6. Run a small sample and inspect cached pickle outputs before scaling.

## Manual + generated variations

A variation entry can contain both a `generator_name` and manual `variations`. YiVal initializes manual variations and then appends generated variations from the generator.

Use this pattern when you want a known baseline prompt plus generated alternatives.

## Chain-of-density summarization

For summarization tasks, use the deterministic fixed prompt generator:

```yaml
variations:
  - name: summarization
    generator_name: chain_of_density_prompt_generator
    variations:
      - value_type: str
        value: You will be given an article; summarize it.
        instantiated_value: You will be given an article; summarize it.
        variation_id: null
```

The generated prompt can be long; ensure the custom function passes article text separately and avoids adding the entire article into the variation itself.

## Self-exemplar math/problem solving

Use `self_exemplar` for a single prompt variation that asks the model to recall related problems and solve the initial problem. It is useful when you need a deterministic prompt construction without provider calls during variation generation.

```yaml
variations:
  - name: qa
    generator_name: self_exemplar
    generator_config:
      start_prompt: Your task is to solve math problems.
      problem_prompt: "<problem statement>"
      relevant_problems_prompt: Recall three relevant problems.
      core_concept_prompt: Identify the core concepts.
      tutorial_prompt: Write a short tutorial.
      end_prompt: Solve the initial problem.
```

## Interactive auto generation commands

- `yival gen` calls YiVal's auto prompt module and asks for input to generate a config.
- `yival task` runs the default task-generation demo.

These are interactive and provider-backed; use them only in an environment where prompts, credentials, and network use are approved.
