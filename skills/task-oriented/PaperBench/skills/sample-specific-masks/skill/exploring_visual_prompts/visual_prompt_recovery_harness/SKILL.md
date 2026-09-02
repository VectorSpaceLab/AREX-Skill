---
name: visual_prompt_recovery_harness
description: Run a bounded mechanism-faithful proxy recovery experiment for visual prompting papers.
---

# Visual Prompt Recovery Harness

Use this skill to assemble a fast recovery experiment for *Exploring Visual Prompts*. The harness should exercise the generated prompt-template, CLIP-output-transformation, and prompt-training skills rather than duplicating their contracts silently. It is suitable for soft-mode proxy recovery when full CLIP training over paper datasets is blocked or too expensive.

## Inputs
- Attempt directory with `module_plan.json`.
- Generated skill root.
- `environment/runtime_handoff.json`.
- A tiny synthetic or real classification dataset.

## Outputs
- `recovery/recovery_result.json` with metric and paper target.
- `recovery/logs/generated_data_item.json`.
- `recovery/logs/training_trace.json`.
- `recovery/logs/generated_skill_invocations.json`.

## Workflow
1. Read the module-plan target instead of hard-coding the paper metric.
2. Construct the smallest dataset that still needs a universal visual prompt.
3. Run frozen-model scoring before prompt optimization.
4. Optimize only prompt parameters and record before/after loss and accuracy.
5. Cross-check that output transformation uses CLIP-style text prompts/cosine probabilities.
6. Mark the result as proxy when full CLIP and datasets are not used, and include explicit mechanism checks.

## Validation
The included script can be imported by recovery code to compute accuracy gain and write validator-compatible JSON fragments.

## Limitations
This skill is not a replacement for a full paper reproduction. It documents a reduced executable recovery when allowed by recovery mode.
