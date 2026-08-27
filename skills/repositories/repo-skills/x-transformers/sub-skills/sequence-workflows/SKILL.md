---
name: "sequence-workflows"
description: "Routes x-transformers wrapper, generation, continuous, latent,
  memory, preference, and specialized sequence workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# sequence-workflows

Use this sub-skill when the task is to choose or operate a higher-level x-transformers wrapper or specialized sequence model rather than designing attention layers from scratch.

## Use this route for

- Autoregressive text generation, beam search, prompt lists, forgetful causal-mask training, prepended embeddings, or cached decoding.
- Non-autoregressive masked-token generation with iterative demasking and optional token critics.
- Continuous sequence models, continuous autoregressive generation, and continuous autoencoding.
- Multi-input token streams where several categorical features are embedded and summed at each position.
- xVal mixed discrete-token and continuous-number modeling.
- Transformer-XL-style segmented recurrence, memories, episodic memories, and test-time-training wrapper flows.
- Belief-state, next-latent, LEJEPA-style latent autoregressive, XM latent-decoder, FreeTransformer, GPTVAE, NeoMLP, DPO, and entropy-based tokenization workflows.

## Do not use this route for

- Selecting attention flags, positional-bias families, normalization, residual, cross-attention, or low-level `Attention` construction. Use `core-models` instead.
- Running or modifying repository `train_*` recipes. Use `training-recipes` instead.
- Importing skills into another agent runtime.

## Read first

- `references/wrapper-contracts.md` for wrapper signatures, shape contracts, generation semantics, and model-selection guidance.
- `references/troubleshooting.md` for predictable assertion failures and recovery steps.

## Operating rules

1. Pick the smallest wrapper that matches the data type: token, continuous, mixed token/number, multi-input token, recurrent-memory, latent, or preference-pair.
2. Build the underlying `TransformerWrapper`, `ContinuousTransformerWrapper`, `XValTransformerWrapper`, encoder, or decoder with `core-models` guidance, then return here for wrapper-specific calls.
3. Keep tensor devices consistent. CPU examples are safe; CUDA can be used when all model inputs, masks, latents, memories, and start tokens are on the same device.
4. Treat `seq_len` carefully: most autoregressive wrappers interpret it as the number of new tokens, while `FreeTransformer.generate` interprets it as the total output length.
5. Before debugging internals, check shape equality constraints in `references/wrapper-contracts.md` and known symptoms in `references/troubleshooting.md`.

## Cross-links inside this skill tree

- For base model construction and attention-feature compatibility, switch to `core-models`.
- For long-running script recipes and dataset prerequisites, switch to `training-recipes`.
