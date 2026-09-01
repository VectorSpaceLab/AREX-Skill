---
name: pplm_recovery_evaluation
description: Use when validating a reduced or full PPLM recovery experiment with numeric metrics and mechanism checks.
---

# PPLM Recovery Evaluation

Use this skill to turn PPLM generation traces into recovery metrics.

## Inputs
- Prompt/attribute items.
- Controlled and uncontrolled outputs.
- Trace flags for attribute model, perturbation, KL, reranking, and frozen base model.
- Paper target metadata.

## Outputs
- Topic or sentiment hit rate.
- Diversity metrics.
- Mechanism checks for recovery_result.json.

## Workflow
1. Canonicalize target words and generated tokens.
2. Compute attribute hit rate.
3. Aggregate diversity.
4. Require mechanism checks for proxy acceptance.
5. Emit validator-compatible JSON.

## Validation
Run `python tests/test_recovery_evaluation.py`.

## Limitations
Reduced proxy implementations must declare that they are not full GPT-2 345M reproduction.
