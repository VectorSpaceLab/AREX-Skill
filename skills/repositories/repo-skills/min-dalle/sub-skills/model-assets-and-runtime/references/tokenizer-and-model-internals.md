# Tokenizer and Model Internals

This reference summarizes the tokenizer, sequence limits, sampling loop, and model shape expectations that matter for setup and debugging. It is intentionally focused on runtime inspection, not public generation recipes.

## TextTokenizer normalization

`TextTokenizer.tokenize(text, is_verbose=False)` applies these transformations in order:

1. Convert emoji to text names with `demojize(..., delimiters=['', ''])`. For example, a rocket emoji becomes the ASCII word `rocket` with typical `emoji` package versions.
2. Lowercase the entire string.
3. Encode to ASCII with `errors='ignore'` and decode back to text. Non-ASCII characters that are not converted by demojize are removed, not replaced.
4. Split only on the literal space character. Empty words are ignored.
5. Byte-pair encode each word.
6. Map each final subword to a vocabulary id, using `<unk>` for missing subwords.
7. Wrap the sequence as `[<s>] + subword_ids + [</s>]`.

Implications:

- Case is not preserved: `HELLO` and `hello` tokenize identically.
- Non-ASCII punctuation and letters may disappear. For example, names containing accents can lose accented characters after the ASCII step.
- Emoji become words before lowercasing, so they can consume multiple text tokens.
- Punctuation is not stripped if it survives ASCII encoding; if the vocabulary lacks the punctuation subword, it maps to `<unk>`.
- Multiple spaces collapse because empty split pieces are skipped.

## BPE merge behavior

For each word, the tokenizer starts with a word-start marker plus characters:

```text
[chr(ord(' ') + 256)] + list(word)
```

The marker is `Ġ` (U+0120). It represents the beginning of a space-prefixed word, not a literal ASCII space.

The merge list is parsed into ordered adjacent-pair ranks. During encoding:

1. Compute all adjacent pairs in the current subword list.
2. Pick the pair with the lowest merge rank.
3. If that pair exists in the merge table, concatenate it into one subword.
4. Repeat until no adjacent pair is mergeable.
5. If `is_verbose=True`, print the final subword list for each word.

The merge order matters: earlier merge lines win. Missing final subwords are mapped to `<unk>` by vocabulary lookup.

## Special tokens and padding assumptions

The tokenizer requires these vocabulary keys:

| Key | Role |
|---|---|
| `<s>` | Start/classification token prepended to every prompt. |
| `</s>` | End/separator token appended to every prompt. |
| `<unk>` | Replacement id for subwords absent from the vocabulary. |

The generation path also treats token id `1` as padding when building attention masks (`text_tokens.not_equal(1)`). The tokenizer itself does not look up a `<pad>` key, so avoid reusing synthetic smoke-test ids as real model ids.

## Text token count and prompt packing

- Maximum text token slots: 64.
- Tokenized prompts longer than 64 ids are truncated to the first 64 ids after the `[<s>] ... [</s>]` wrapping.
- Prompt packing creates a two-row text tensor initialized with pad id `1`:
  - row 0 contains only the first and last token ids in the first two positions;
  - row 1 contains the full prompt tokens up to the 64-token limit.
- For a grid with `image_count = grid_size ** 2`, those two rows are expanded to `2 * image_count` rows before decoder sampling. This supports the unconditional/conditional logit mixing used by superconditioning.

## Encoder shape facts

The encoder is a BART-like stack with token and position embeddings:

| Shape/fact | Value |
|---|---|
| Input `text_tokens` | `(batch, 64)` long tensor. In generation, batch is initially 2, then expanded to `2 * image_count`. |
| Token embedding table | `(text_vocab_count, embed_count)`. |
| Position embedding table | `(64, embed_count)`. |
| Attention mask | `(batch, 1, 1, 64)`, true where token id is not `1`. |
| Output `encoder_state` | `(batch, 64, embed_count)`. |
| Mega constants | 24 layers, 32 heads, `embed_count=2048`, `glu_embed_count=4096`, `text_vocab_count=50272`. |
| Mini constants | 12 layers, 16 heads, `embed_count=1024`, `glu_embed_count=2730`, `text_vocab_count=50264`. |

## Decoder shape and sampling facts

The decoder samples image tokens autoregressively:

- Image token count is fixed at 256.
- `image_count = grid_size ** 2`.
- The working image-token tensor has shape `(image_count, 257)`: one initial column plus 256 sampled columns.
- The initial token value is `2 ** 14 - 1` (16383), and sampled tokens fill columns 1 through 256.
- Decoder token positions are `0..255`.
- The key/value attention cache has shape `(layer_count, image_count * 4, 256, embed_count)`. The factor of 4 stores keys and values for both unconditional and conditional halves.
- Decoder token embeddings use `image_vocab_count + 1` entries, but sampling logits are sliced to the first `2 ** 14` entries.
- `top_k` is used as an index into sorted logits; keep it in `1..16384` unless a higher-level generation wrapper validates differently.
- `temperature` is a divisor; use a positive value.
- If `seed > 0`, the sampling loop calls `torch.manual_seed(seed)` for reproducibility.

Logit mixing and sampling:

```text
mixed_logits = unconditional_logits * (1 - supercondition_factor)
             + conditional_logits   * supercondition_factor
```

Then the sampler keeps the top-k logits, subtracts the row maximum for numerical stability, divides by temperature, exponentiates, masks non-top-k entries, and draws one token per image with `torch.multinomial`.

## VQGanDetokenizer shape facts

The detokenizer maps 256 image tokens per image into 256x256 RGB tiles and then composes a grid.

| Shape/fact | Value |
|---|---|
| VQGAN vocabulary count | `2 ** 14` = 16384. |
| VQGAN embedding width | `2 ** 8` = 256. |
| Per-image latent grid | `16 x 16` tokens. |
| Per-image pixel tile | `256 x 256 x 3`. |
| Input for a grid | `(grid_size ** 2, 256)` token ids. |
| Non-seamless output | One stitched grid with shape `(grid_size * 256, grid_size * 256, 3)` and float values clipped to `0..255`. |
| Seamless output | Tokens are rearranged into one `grid_size * 16` latent map before decoding, producing a single seamless grid image rather than independently decoded tiles. |

The detokenizer infers `grid_size` as `int(sqrt(number_of_images))`, so the number of image-token rows must be a perfect square. Keep `grid_size` consistent from generation through detokenization.
