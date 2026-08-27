# Text conditioning

## T5 path
The bundled T5 helper uses Hugging Face transformers for tokenization and encoding.

Important constants:
- `MAX_LENGTH = 256`
- `DEFAULT_T5_NAME = 'google/t5-v1_1-base'`

Encoding behavior:
- tokenization uses longest padding and truncation at 256 tokens
- the encoder output is zeroed where padding tokens are masked out
- `return_attn_mask=True` returns a boolean attention mask alongside the embeddings

## Shape contracts
When using raw text strings:
- the number of captions must equal the image batch size
- the model derives `text_embeds` and `text_masks` internally

When using precomputed tensors:
- `text_embeds` must be shaped `[batch, seq_len, d_model]`
- `text_masks` must be shaped `[batch, seq_len]` when provided
- `text_embeds.shape[-1]` must match the model’s configured `text_embed_dim`
- `seq_len` should not exceed 256

If a `text_masks` tensor is not supplied, the model can infer a mask from non-zero embedding rows, but explicit masks are safer for padded or custom-precomputed inputs.

## Model-size implications
- `get_encoded_dim(name)` can read the encoder config without loading encoder weights.
- Actual text encoding still loads the tokenizer and encoder for the selected model name.
- The tokenizer/model pair is cached per name in module-level state.

## Network and cache implications
- The first text-encoding call may fetch tokenizer, config, or encoder weights from the Hugging Face ecosystem.
- If the cache is missing and network access is unavailable, text encoding will fail.
- Precomputed `text_embeds` / `text_masks` avoid that dependency during training or sampling.

## Model-name note
The library default is `google/t5-v1_1-base`, while example configs may override this to a larger T5 variant. Treat the chosen name as explicit input, not an implied default.
