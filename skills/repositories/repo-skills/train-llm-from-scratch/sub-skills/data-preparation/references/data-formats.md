# Data Formats And Loader Contracts

This repository uses four data shapes. They are intentionally different: a file
that is valid for one stage is not interchangeable with another.

## Shared Tokenization Facts

| Fact | Contract |
|---|---|
| Tokenizer | OpenAI `tiktoken` encoding `r50k_base`. |
| End-of-text token | `EOT_ID = 50256`, rendered as `<|endoftext|>`. |
| Model vocab size | Training configs commonly use `50304`, padding above tokenizer ids. Raw data should normally stay in `0..50256`; generated model ids may include padding ids, but data files should not. |
| Chat roles | `<|user|>\n`, `<|assistant|>\n`, and `<|system|>\n` are plain text, not registered special tokens. |
| Reasoning tags | `<think>...</think><answer>N</answer>` are ordinary text tokens used by math SFT and verifier rewards. |

## 1. Flat Pretraining HDF5

**Use for:** base language-model pretraining only.

**Schema:** one HDF5 dataset named `tokens`.

| Field | Required shape | dtype | Meaning |
|---|---:|---|---|
| `tokens` | `(num_tokens,)` | integer, usually `int32` | A single flat stream of token ids. Each source document is followed by EOT `50256`. |

**Important invariants**

- The dataset is one-dimensional, not `(N, context_length)`.
- Values should be nonnegative and should not exceed `50256` for data generated
  from `r50k_base` text plus EOT.
- EOT separators should be present in real Pile-derived files. A tiny synthetic
  smoke file may have few separators, but absence of EOT in real data suggests
  a preprocessing bug.
- The base batch iterator slices non-overlapping shuffled windows of length
  `context_length + 1`, then returns `xb = window[:-1]` and `yb = window[1:]`.
  Therefore the HDF5 needs at least `context_length + 1` tokens for one sample.

## 2. Packed SFT HDF5

**Use for:** supervised fine-tuning with prompt-masked next-token loss.

**Schema:** two aligned HDF5 datasets: `tokens` and `loss_mask`.

| Field | Required shape | dtype | Meaning |
|---|---:|---|---|
| `tokens` | `(num_rows, context_length)` | integer, usually `int32` | Packed chat token ids. |
| `loss_mask` | exactly same shape as `tokens` | integer/bool, usually `int8` | `1` only where the model should learn to produce assistant completion tokens; `0` on user/system prompts and role headers. |

**Chat and mask contract**

A single user/assistant exchange is rendered as ordinary text with EOT turn
terminators:

```text
<|user|>
{user content}<|endoftext|><|assistant|>
{assistant content}<|endoftext|>
```

The aligned `loss_mask` is:

- `0` on role headers.
- `0` on user/system content and their EOT terminators.
- `1` on assistant content tokens.
- `1` on the assistant turn's EOT, so SFT teaches the model to stop.

For GSM8K SFT examples, the assistant completion is reformatted as:

```text
<think>reasoning without calculator annotations</think><answer>final_number</answer>
```

**Packing contract**

`pack_examples(examples, context_length)` concatenates `(ids, loss_mask)`
examples, uses EOT as the separator already present in each encoded chat, slices
full rows of exactly `context_length`, and drops any trailing partial row. This
means a valid packed row may contain portions of multiple examples, but `tokens`
and `loss_mask` must remain aligned element by element.

**Loader behavior**

The SFT iterator reads whole rows, shards row indices by DDP rank, optionally
shuffles, and yields `(tokens, loss_mask, epoch)`. It does not derive a mask from
text at training time; a wrong stored mask directly trains the wrong tokens.

## 3. Preference JSONL

**Use for:** reward-model training and DPO/ORPO/KTO.

**Schema:** UTF-8 JSON Lines; one object per line.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `prompt` | nonempty string | yes | Shared prompt/context. |
| `chosen` | nonempty string | yes | Preferred assistant response. |
| `rejected` | nonempty string | yes | Less-preferred assistant response. |

**Important invariants**

- `chosen` and `rejected` must differ after string comparison. Degenerate pairs
  carry no preference signal and should be removed before training.
- Both sides are encoded as chat conversations with the same user prompt and one
  assistant response. The response mask covers only the assistant response side;
  reward-model sequence lengths point to the last real token.
- Batches are right-padded with EOT. This is safe because the Transformer is
  causal: the last real token cannot attend to padding that comes after it.
- Preference sequence length can be truncated by the stage `max_len`. If the
  common prompt is very long, truncation may leave little or no response signal.

## 4. RL Prompt JSONL And Arithmetic Curriculum

**Use for:** PPO and GRPO/RLVR prompt iterators.

**Schema:** UTF-8 JSON Lines; one object per line.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `prompt` | nonempty string | yes | User question/prompt for rollout. |
| `gold` | number or `null` | yes by convention | Numeric answer for verifier reward, or `null` when no verifier label is available. |

**Files commonly produced**

| File | Purpose |
|---|---|
| `rl_prompts_train.jsonl` | GSM8K train prompts for PPO/GRPO. |
| `rl_prompts_test.jsonl` | Held-out GSM8K prompts for evaluation. |
| `arithmetic_prompts.jsonl` | Programmatic arithmetic warm-up curriculum for GRPO. |

**Arithmetic curriculum shape**

The generated arithmetic prompt is normally a direct expression such as
`What is 13 + 29?`, `What is 9 - 4?`, or `What is 7 * 6?`, with `gold` equal to
the numeric result. Use `validate_rl_prompts_jsonl.py --arithmetic-sanity` to
check rows that are intended to be this curriculum.

**Loader behavior**

The prompt iterator loads rows into memory, shards them by DDP rank, and yields
lists of `prompts_per_iter` rows forever. It does not validate that `gold` is
numeric during iteration; invalid gold values produce verifier failures or zero
reward later.
