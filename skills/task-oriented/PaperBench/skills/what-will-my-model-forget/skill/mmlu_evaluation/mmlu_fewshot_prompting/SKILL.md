---
name: mmlu_fewshot_prompting
description: Build MMLU zero-shot and five-shot prompts while hiding the test answer from the model query.
---

# mmlu_fewshot_prompting

Use this skill when a recovery or evaluation task needs the MMLU mechanism represented by this module. Do not use it as a substitute for a full model evaluation unless the run explicitly declares a reduced proxy target.

## Inputs
Inputs are JSON-compatible dictionaries following the module document contract. Required fields are validated by the script in `scripts/`.

## Outputs
Outputs are JSON-compatible dictionaries with normalized labels, prompts, scores, or recovery artifacts. Downstream modules should consume these outputs instead of parsing free-form text.

## Workflow
1. Read the paper profile and module plan to confirm the selected target.
2. Call the script or import the helper functions from `scripts/`.
3. Preserve the boundary between item construction, prompt construction, scoring, and recovery logging.
4. Run the validation command after changes: `python <distiller>/module-to-skill/scripts/validate_skill_tree.py <skill_dir> --run-tests`.

## Limitations
This skill captures the evaluation mechanism, not the full hosted GPT-3 runtime or the full private benchmark distribution. Soft-mode recovery must label reduced results as proxy evidence.


## Refinement Note
Cycle 03 confirms the test answer remains hidden while demonstration answers remain visible.
