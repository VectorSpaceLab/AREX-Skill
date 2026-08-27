# Enhancers reference

YiVal enhancers run after experiment evaluation/selection and can create improved prompt or combination candidates. They are usually provider-backed and should be treated as opt-in cost-bearing workflows.

## Registry ids

| Enhancer id | Config class | Main use |
| --- | --- | --- |
| `openai_prompt_based_combination_enhancer` | `OpenAIPromptBasedCombinationEnhancerConfig` | Iterate prompt/combination improvement with an OpenAI model and optional stop conditions. |
| `optimize_by_prompt_enhancer` | `OptimizeByPromptEnhancerConfig` | Generate new prompts from previous prompts and evaluation feedback using meta-instructions. |
| `pe2_enhancer` | `PE2EnhancerConfig` | Prompt engineering enhancement with full prompt descriptions and controlled prompt-instruction behavior. |

## `openai_prompt_based_combination_enhancer`

```yaml
enhancer:
  name: openai_prompt_based_combination_enhancer
  openai_model_name: gpt-4
  max_iterations: 3
  stop_conditions: null
  average_score: null
```

Use when an OpenAI-backed loop should improve combinations from prior evaluation results.

## `optimize_by_prompt_enhancer`

```yaml
enhancer:
  name: optimize_by_prompt_enhancer
  enhance_var:
    - task
  model_name: gpt-4
  max_iterations: 2
  head_meta_instruction: |-
    Here are prior prompts and their evaluation results.
  end_meta_instruction: |-
    Propose a new prompt that should score better.
  optimation_task_format: null
```

Use `enhance_var` to list variation names the enhancer may change. Keep meta-instructions specific to the task and metrics.

## `pe2_enhancer`

```yaml
enhancer:
  name: pe2_enhancer
  enhance_var:
    - task
  enable_prompt_instruction: true
  full_prompt_description: "prompt.format(question=question)"
  max_iterations: 1
  batch_size: 3
  step_size: null
  max_token: 200
```

Use when you want PE2-style prompt improvement tied to a full prompt description.

## Enhancement workflow

1. Prove the base experiment with `display=False`, a tiny dataset, and at least one reliable evaluator.
2. Configure AHP or another selector so the enhancer can see useful feedback.
3. Set `max_iterations` low for the first run.
4. Confirm provider credentials and budget.
5. Save output pickles and inspect `experiment.enhancer_output`.

## Limitations

- Enhancers are not a substitute for good evaluator prompts and expected results.
- Provider failures can leave partial state; cache or save outputs before scaling.
- Keep `enhance_var` aligned with actual `StringWrapper` names.
