---
name: vpt_prompt_token_insertion
description: Build shallow and deep Visual Prompt Tuning token sequences for Transformer-style image embeddings.
---

# VPT Prompt Token Insertion

Use this skill when implementing or checking Visual Prompt Tuning (VPT) token formatting for a vision Transformer or a reduced VPT proxy. Do not use it to compute losses, choose hyperparameters, or emit classification metrics.

## Inputs

- A batch of token embeddings shaped as `[batch, 1 + patches, hidden]` where the first token is `[CLS]`.
- Prompt embeddings shaped as `[num_prompt_tokens, hidden]`.
- Optional deep prompt embeddings shaped as `[layers, num_prompt_tokens, hidden]`.
- Configuration metadata with `location="prepend"`, prompt count, hidden size, and whether prompts are shallow or deep.

## Outputs

- Prompt-augmented token batches shaped as `[batch, 1 + prompts + patches, hidden]`.
- Metadata describing prompt count, hidden size, and placement.
- Validation errors for unsupported prompt locations or shape mismatches.

## Workflow

1. Confirm the input sequence has `[CLS]` plus at least one image token.
2. Validate the prompt hidden size against the token hidden size.
3. Preserve `[CLS]` at position 0 and preserve image-token order.
4. Broadcast prompt embeddings across the batch and insert them immediately after `[CLS]`.
5. For deep VPT, replace the existing prompt-token slots with the layer-specific prompt bank while keeping `[CLS]` and image tokens unchanged.
6. Return formatting metadata; leave training, pooling, and evaluation to downstream skills.

## Validation

Run `python tests/test_prompt_ops.py` from this skill directory, or run the Distiller skill validator with `--run-tests`.

## Limitations

This skill implements the paper's default prepend-token VPT mechanism. Pixel-padding prompt variants and pooling choices are intentionally outside this module's contract.
