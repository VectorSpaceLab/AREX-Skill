---
name: residual_logit_lens
description: Apply logit-lens unembedding and additive residual contribution checks for mechanistic transformer circuit analysis.
---

# Residual Logit Lens

Use this skill when you need to inspect how a transformer's residual stream or named additive residual components affect output logits. It is appropriate for attention-only or simplified transformer-circuit analysis where the residual stream is treated as a linear communication channel. Do not use it as a standalone causal proof when component activations are not defined.

## Inputs

- A residual state matrix shaped `positions x features`.
- An unembedding matrix shaped `features x vocabulary`.
- Optional named residual components with the same shape as the residual state.

## Outputs

- Full logits for every position.
- Optional per-component logits.
- A reconstruction error showing whether component logits sum to the full logits.

## Workflow

1. Validate that all matrices are rectangular and dimension-compatible.
2. Compute `logits = residual @ unembedding`.
3. For each named component, compute `component @ unembedding`.
4. If components are meant to sum to the residual, compare the sum of component logits to the full logits.
5. Report the maximum absolute difference and preserve component names.

## Validation

Run `python tests/test_logit_lens.py` or validate the full tree with:

```bash
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/module-to-skill/scripts/validate_skill_tree.py <skill_dir> --run-tests
```

## Limitations

This skill uses standard-library Python lists for tiny or moderate matrices. For large models, use the same contracts with a tensor library and avoid materializing unnecessary dense intermediates.
