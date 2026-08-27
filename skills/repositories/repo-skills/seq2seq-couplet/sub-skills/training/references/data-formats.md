# Data Formats

## Purpose

Read this when you need to prepare the sentence-pair files or the vocabulary
file for training.

## File layout

The training reader expects three kinds of files:

- aligned input sentences,
- aligned target sentences,
- the shared vocabulary file.

Each sentence pair is one line per file. The line numbers must align exactly.

## Tokenization

- Tokens are space-separated.
- Blank tokens are ignored.
- The reader truncates a line to `max_len - 1` tokens before appending the end
  token.
- The input side gets the end token appended.
- The target side gets `<s>` prepended and the end token appended.

## Vocabulary order

The first two vocabulary entries must be:

1. `<s>`
2. `</s>`

The inference path treats those as the start and end tokens. If you change the
order, the checkpoint no longer matches the text-generation logic.

## Minimal example

Vocabulary file:

```text
<s>
</s>
天
地
风
云
```

Input file:

```text
天 地
山 水
```

Target file:

```text
风 云
云 风
```

## Reader behavior to remember

- Unknown tokens are silently dropped during encoding.
- `SeqReader.data_size` uses integer division by batch size.
- `read()` yields padded batches forever and reshuffles when the data position
  wraps.
- Padding uses `0`, which is the `<s>` token index in the verified vocabulary
  order.

## Why this matters

Most training failures on this repo are data-layout failures rather than graph
failures. If the vocabulary order or line alignment is wrong, the model can
still build but it will train on the wrong ids or skip examples silently.
