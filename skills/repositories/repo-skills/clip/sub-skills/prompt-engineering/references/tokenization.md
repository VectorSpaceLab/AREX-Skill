# Tokenization

CLIP's public text entry point is `clip.tokenize(texts, context_length=77, truncate=False)`. It wraps `SimpleTokenizer`, adds start/end tokens, pads to a fixed context length, and returns a 2-D integer tensor for `model.encode_text`.

## Public Contract

- `texts` can be a single string or a list of strings.
- `context_length` defaults to `77`; all released CLIP models use this length.
- `truncate=False` raises a `RuntimeError` when any encoded prompt is longer than the context length.
- `truncate=True` cuts tokens to the context length and ensures the final token is end-of-text.
- The returned tensor shape is `[number_of_texts, context_length]`.
- Modern PyTorch returns an int32 tensor; older PyTorch versions before 1.8 returned a long tensor because earlier indexing operations required long indices.

The text encoder selects the feature at the end-of-text position, so preserving the end token matters when truncating.

## SimpleTokenizer Behavior

`SimpleTokenizer.encode` performs these steps:

1. Fix Unicode text with `ftfy.fix_text`.
2. HTML-unescape twice.
3. Strip leading/trailing whitespace.
4. Collapse repeated whitespace to a single space.
5. Lowercase the text.
6. Split text with a regex that keeps special start/end tokens, English contractions, letter spans, number spans, and punctuation/non-space symbols.
7. Encode UTF-8 bytes through a reversible byte-to-Unicode mapping.
8. Apply BPE merges from the bundled `bpe_simple_vocab_16e6.txt.gz` vocabulary.

Practical consequences:

- Tokenization is case-insensitive for normal text: `Cat`, `cat`, and `CAT` map the same after lowercasing.
- Whitespace-only differences are collapsed.
- HTML entities and malformed Unicode are cleaned before BPE.
- Punctuation and uncommon strings can consume extra tokens; long taxonomic names, URLs, or generated captions can exceed the 77-token limit quickly.
- The tokenizer avoids unknown tokens by byte encoding, but that does not mean every language or symbol is semantically reliable for CLIP.

## Context-Length Budget

`context_length=77` includes special tokens. A prompt can be too long even when it looks short in characters because BPE splits uncommon words and punctuation into multiple tokens.

Use a dry run before model inference:

```python
import clip

texts = ["a photo of a very long generated class name."]
tokens = clip.tokenize(texts, context_length=77, truncate=False)
print(tokens.shape)
```

For generated templates, dry-run every expanded prompt, not just the template alone.

## Truncation Policy

Prefer shortening prompts/classes over truncation when class identity appears near the end of the prompt. Truncation is acceptable only when the caller deliberately chooses it and verifies that the retained text still expresses the class.

Recommended order when `RuntimeError: Input ... is too long for context length 77` appears:

1. Shorten verbose templates.
2. Replace long class descriptions with concise labels plus a short disambiguator.
3. Remove redundant style phrases from template ensembles.
4. Split a multi-concept class into separate class labels if the taxonomy is overloaded.
5. Use `truncate=True` only for exploratory runs or when the important class words are known to remain before the cut.

## Batching and Devices

`clip.tokenize` returns a CPU tensor. Move it to the model device before encoding:

```python
text_tokens = clip.tokenize(texts).to(device)
text_features = model.encode_text(text_tokens)
```

Common mistakes:

- Calling `.cuda()` in CPU-only code; use `.to(device)` instead.
- Moving the model to CUDA but leaving token tensors on CPU.
- Concatenating prompt batches created with different `context_length` values.
- Passing raw strings directly to `model.encode_text`; it expects token tensors.

## Decode Is Diagnostic Only

`SimpleTokenizer.decode(tokens)` reconstructs approximate text from token ids and replaces BPE word-end markers with spaces. Use it for debugging tokenization, not as a source of canonical prompt text.

## Safe Prompt Expansion Check

Before building classifier weights, validate templates:

- Each standard template contains exactly one `{}` placeholder.
- Formatting with every class name succeeds.
- Tokenization succeeds with `truncate=False` unless truncation was explicitly requested.
- The expanded prompt list is non-empty.
- Class order is recorded because weight columns follow class order.
