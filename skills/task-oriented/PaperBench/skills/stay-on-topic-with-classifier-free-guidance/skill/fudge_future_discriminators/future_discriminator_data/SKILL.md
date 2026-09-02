---
name: future_discriminator_data
description: Build prefix-level future-discriminator examples for FUDGE-style controlled generation from completed token sequences and sequence/target-word labels.
---

# Future Discriminator Prefix Data

Use this skill when implementing or testing FUDGE-like future discriminators. It converts completed token sequences into prefix examples whose labels indicate whether an attribute or target word will hold in the completed future.

Do not use this skill to perform decoding or choose output tokens; its output is only training/evaluation data for a discriminator.

## Inputs
- Completed token sequences as lists of tokens.
- `mode`: `whole_sequence` or `future_suffix`.
- For `whole_sequence`: one binary label per sequence.
- For `future_suffix`: a target token/word.

## Outputs
A JSON-compatible object with `examples` and `metadata`. Each example contains `prefix_tokens`, `label`, `position`, `target`, and `source_sequence_id`.

## Workflow
1. Normalize tokens consistently before calling the script if case-insensitive labels are wanted.
2. Expand every non-empty prefix of every completed sequence.
3. In whole-sequence mode, copy the sequence attribute to every prefix.
4. In future-suffix mode, label a prefix positive if the target appears in the remaining suffix including the current prefix-final token.
5. Use the examples to train or audit a lightweight future discriminator.

## Validation
Run `python tests/test_prefix_data.py` from this skill directory.

## Limitations
The helper operates on already-tokenized sequences. It does not train a neural model and does not read the original paper repository.
