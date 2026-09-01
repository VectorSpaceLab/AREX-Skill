---
name: cot_prompt_templates
description: Build standard, chain-of-thought, and ablation few-shot prompts with auditable prompt structure metadata.
---

# Chain-of-Thought Prompt Templates

Use this skill when you need to construct prompts for the chain-of-thought prompting paper or for a recovery experiment that compares direct few-shot answers against reasoning-before-answer exemplars. Do not use it to run an LLM, compute a task answer, or score a prediction.

## Inputs

- A JSON list of exemplars. Every exemplar needs `question` and `answer`; chain-of-thought and ablation modes also need `reasoning`.
- A target question string.
- A mode: `standard`, `chain_of_thought`, `equation_only`, `variable_compute_only`, or `reasoning_after_answer`.

## Outputs

- Prompt text containing rendered exemplars and the target question.
- Metadata describing mode, exemplar count, reasoning placement, and whether final-answer markers are present.

## Workflow

1. Select the prompt mode that matches the comparison being run.
2. Validate exemplar fields before rendering; reject missing reasoning in chain-of-thought modes.
3. Render exemplars as `Q:` and `A:` blocks.
4. For `chain_of_thought`, place reasoning before `The answer is ...`.
5. For `standard`, omit reasoning and include only the direct answer.
6. For ablations, preserve the structural difference being tested: equations only, useless variable-compute padding, or reasoning after the answer.
7. Append the target question and `A:` prefix without including the target answer.

## Validation

Run:

```bash
python scripts/cot_prompt_templates.py --self-test
python -m unittest discover -s tests
```

The tests verify that standard prompts omit reasoning, chain-of-thought prompts include reasoning before the final answer, and ablation modes are structurally distinct.

## Limitations

This skill does not infer missing reasoning, call a model, or canonicalize answers. Pair it with `cot_answer_extraction` and `cot_equation_calculator` for evaluation or recovery work.
