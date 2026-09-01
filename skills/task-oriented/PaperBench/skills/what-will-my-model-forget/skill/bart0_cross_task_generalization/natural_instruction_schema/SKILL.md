---
name: natural_instruction_schema
description: Normalize crowdsourcing task instructions into validated Natural Instructions records for cross-task generalization experiments.
---

# Natural Instruction Schema

Use this skill when a recovery or benchmark harness needs to turn task templates into the structured Natural Instructions format from the paper. Do not use it to solve task instances directly or to mix train and evaluation examples.

## Inputs
- `task_id`, `dataset`, and `category` strings.
- Instruction fields: `definition`, `prompt`, optional `things_to_avoid`, optional `emphasis`, positive examples, negative examples, and instances.
- Examples and instances represented as dictionaries with `input` and `output` strings.

## Outputs
- A JSON-compatible task record with normalized fields.
- Validation errors for missing task identity, absent task-defining text, or missing instances.

## Workflow
1. Read raw crowdsourcing-template content and split it into minimal subtask fields before calling the script.
2. Call `scripts/natural_instruction_schema.py` or import `build_instruction_record`.
3. Keep examples separate from evaluation instances; examples are instructional content, not predictions.
4. Preserve empty negative examples when the source task lacks them, as with QASC in the paper.
5. Save the resulting record for split and encoding modules.

## Validation
Run `python tests/test_natural_instruction_schema.py` or validate the whole skill with `validate_skill_tree.py --run-tests`.

## Limitations
This skill does not fetch Natural Instructions data or infer missing instruction text. It only normalizes content supplied by the caller.
