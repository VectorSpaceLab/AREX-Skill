---
name: masked_program_embedding
description: Build BAR-style masked target embeddings and universal tanh-bounded programs while preserving protected target-domain data.
---

# Masked Program Embedding

Use this skill when implementing adversarial reprogramming or a BAR proxy experiment that must embed smaller target-domain arrays in a larger source-domain input and add a universal program only outside the protected region.

Do not use it for ordinary data augmentation or for perturbations that are allowed to alter the target sample content.

## Inputs

- A batch of same-shaped numeric target samples.
- A source canvas shape with the same rank as each sample.
- An embedding offset, or `None` to center the sample.
- Program parameters `W` with the source canvas shape.

## Outputs

- Embedded batch `X`.
- Binary mask `M`, with `0` on target data and `1` on programmable cells.
- Program `P = tanh(W*M)`.
- Programmed batch `X + P`.

## Workflow

1. Validate that every target sample fits inside the source canvas.
2. Place every target sample at the same offset in a zero canvas.
3. Construct a mask that protects exactly the embedded target region.
4. Apply the universal tanh-bounded program outside that region.
5. Verify protected values are unchanged before passing data to a black-box model.

## Validation

Run `python tests/test_masked_program_embedding.py` or validate the skill tree with `validate_skill_tree.py --run-tests`.

## Limitations

This skill does not choose label mappings or optimize `W`; it only provides the input transformation contract used by BAR.
