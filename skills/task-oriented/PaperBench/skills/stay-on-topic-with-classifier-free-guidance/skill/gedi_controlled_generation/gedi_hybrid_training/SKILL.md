---
name: gedi_hybrid_training
description: Compute and test GeDi's hybrid discriminative-generative objective with a deterministic tiny optimizer step.
---

# GeDi Hybrid Training

## When to use
Use this skill when training or validating a class-conditional LM as a GeDi, especially when checking the loss decomposition between generative likelihood and discriminative posterior classification.

## Inputs
- Desired and undesired class log probabilities or a tiny parameterized proxy.
- True class label.
- Generative negative log likelihood.
- Hybrid weight `lambda`.
- Optional learning rate for a reduced optimizer step.

## Outputs
- Discriminative loss.
- Generative loss.
- Hybrid loss.
- Training trace with `params_before`, `params_after`, and before/after loss.

## Workflow
1. Compute GeDi posterior over classes for the full sequence.
2. Compute discriminative cross-entropy for the true class.
3. Compute or consume generative NLL for the true class.
4. Combine with `lambda * generative + (1-lambda) * discriminative`.
5. If doing reduced recovery, run a real optimizer update on tiny trainable parameters and record the trace.

## Validation
Run:

```bash
python tests/test_training.py
```

## Limitations
The included script is a deterministic proxy for objective validation, not full GPT-2/GeDi checkpoint training.
