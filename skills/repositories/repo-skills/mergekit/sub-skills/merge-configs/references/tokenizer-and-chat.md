# Tokenizer and chat-template configuration

Tokenizer construction is optional and is selected independently from the merge
method. It changes embedding inputs when enabled, so validate vocabulary and
embedding behavior rather than checking only that tokenizer files exist.

## Modern versus legacy selection

Use one of these mutually exclusive top-level fields:

```yaml
tokenizer:
  source: union       # union, base, or a model reference
  tokens:
    <|new_token|>:
      source: ./chat-model
      force: true
  pad_to_multiple_of: 16
```

or the compatibility form:

```yaml
tokenizer_source: union  # union, base, or a model reference
```

`MergeConfiguration` rejects a document containing both. The modern
`tokenizer` field is a `TokenizerConfig` with:

- `source`: `union` (default), `base`, or a model reference;
- `tokens`: an optional map from output token string to `TokenEmbeddingConfig`;
- `pad_to_multiple_of`: an optional positive multiple used for embedding/config
  padding.

Legacy `tokenizer_source` selects only the output tokenizer. It does not expose
per-token sources, `force`, or padding controls. If neither field is present,
mergekit does not build a merged tokenizer; the default `--copy-tokenizer`
behavior tries to copy/serialize a donor tokenizer after the model merge.

## Vocabulary source behavior

- `base` uses the base tokenizer, or the first referenced model when no base is
  set.
- `union` starts from the base tokenizer and adds usable vocabulary and added
  tokens from referenced model tokenizers. Entries at or beyond a model's
  configured vocabulary size are treated as unused and skipped.
- A model reference source loads that model's tokenizer as the output
  vocabulary. It must be accessible, but it need not be a tensor-merge input.
  A model used as a per-token embedding donor is different: it must be one of
  the merge references so its embedding permutation is available.
- A tokenizer load failure for a non-base model is logged and that model is
  treated as having the base tokenizer for permutation purposes; do not treat
  this warning as proof that token semantics match.

The union builder preserves the base tokenizer's ordering and adds new regular
and added tokens. Token names listed under `tokens` are added to the output
vocabulary even when absent from the selected source, which is useful for new
special tokens.

## Embedding fill and force rules

When a tokenizer is built, every input embedding matrix is permuted to the
output vocabulary before the selected merge method receives it. For an output
token missing in an input model:

1. use the base model's embedding when the base has the token;
2. otherwise use the only model that has it;
3. otherwise use an average of available embeddings, or zeros when no model has
   it.

For a token present in an input model, its own embedding remains the default and
is then merged normally. Therefore a union token's final embedding is not
simply “taken from the donor” unless the configuration forces that behavior.

A token entry can override this:

```yaml
tokenizer:
  source: union
  tokens:
    <|im_start|>:
      source: ./chatml-model
      force: true
    <|alias|>:
      source:
        kind: model_token
        model: ./chatml-model
        token: <|im_start|>
      force: true
    <|blank|>:
      source:
        kind: zero
      force: true
```

Supported `source` forms are a model reference, `{kind: zero}`, or
`{kind: model_token, model: ..., token: ...}` / `token_id: ...`. A
`model_token` must specify exactly one of `token` and `token_id`; its model must
be among the merge references and the token/id must be valid. `force: true`
replaces an existing token's embedding in every input with the computed source
embedding before merging. Without force, the override supplies the embedding
where needed but does not replace an input's existing embedding.

If a configured model source is not in the merge, or a requested donor token is
absent/out of range, expect an assertion or runtime failure during embedding
planning. Keep explicit donor models in `models`/`slices` and validate the
spelling of special tokens.

## Padding and output checks

`pad_to_multiple_of` pads the model embedding tensor and updates the output
model config vocabulary size to the padded size. The serialized tokenizer's
actual vocabulary remains its real token count; added embedding rows are filled
with the mean of existing rows. Check both values:

- tokenizer `len(get_vocab())` equals the real vocabulary;
- model config `vocab_size` and embedding row count equal the padded size.

All embedding widths must match. A width mismatch is an architecture or model
compatibility problem, not a tokenizer setting to paper over.

## Chat templates

Set `chat_template` at the top level:

```yaml
chat_template: chatml
```

Accepted forms:

- `auto`: load templates from referenced tokenizers and choose the most common
  non-empty template; if none load, leave the template unset and log the issue;
- built-ins: `alpaca`, `chatml`, `exaone`, `llama3`, and `mistral`;
- a literal Jinja template string containing braces and at least 20 characters.

A short unknown name or a string without a Jinja marker fails with
`Invalid chat template`. The template is assigned when the tokenizer is saved.
If there is no built/built-copied tokenizer, mergekit warns that the requested
chat template cannot be saved; use a tokenizer source or keep
`--copy-tokenizer` enabled.

`auto` is a plurality choice, not a semantic merge: if models have different
valid templates, explicitly select a built-in or provide literal Jinja. In
Transformers configurations that store multiple templates, the default entry
is used for auto selection.

## Tokenizer-focused validation

After a successful run:

1. load the output tokenizer with the same Transformers major version;
2. check expected union/base/model vocabulary and added special tokens;
3. compare forced token vectors against the intended donor or token id;
4. check padding rows and output `vocab_size` when requested;
5. check `tokenizer.chat_template` contains the built-in marker or literal;
6. confirm tokenizer files were actually written and not merely copied with a
   stale donor configuration.

The normalization helpers recognize common GPT-2/Qwen word-start `Ġ` markers,
SentencePiece Llama/T5/Gemma `▁` markers, and special-token names. Unknown
fast-tokenizer classes fall back to `Ġ` with a warning; if a union behaves
unexpectedly, treat that warning as a tokenizer compatibility gap.
