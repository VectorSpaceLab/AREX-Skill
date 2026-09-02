---
name: reduced_instruction_training_evaluation
description: Execute a bounded instruction-conditioned training proxy and ROUGE-L evaluation for BART0-style recovery.
---

# Reduced Instruction Training And Evaluation

Use this skill when full Natural Instructions BART fine-tuning is blocked but soft-mode recovery permits a declared reduced proxy. Do not present this proxy as the paper’s full result.

## Inputs
- Normalized tasks, cross-task split metadata, and encoded instances from the other generated skills.
- Candidate outputs and references for tiny seen and unseen tasks.
- Initial scalar parameters controlling instruction-field and input-overlap weights.

## Outputs
- A training trace with `loss_before`, `loss_after`, `params_before`, `params_after`, and optimizer state evidence.
- Predictions, references, ROUGE-L, and mechanism checks.
- JSON artifacts suitable for `validate_recovery_experiment.py`.

## Workflow
1. Score candidate outputs with an instruction-aware overlap model.
2. Compute a seen-task ranking loss that favors references over distractors.
3. Apply one deterministic optimizer step to trainable weights.
4. Select the highest-scoring unseen-task candidate after the update.
5. Compute ROUGE-L and write recovery evidence.

## Validation
Run `python tests/test_reduced_instruction_training_evaluation.py` or validate with `validate_skill_tree.py --run-tests`.

## Limitations
The optimizer is a transparent scalar proxy, not BART-base. It demonstrates the paper mechanism under bounded runtime rather than reproducing Table 4 at scale.
