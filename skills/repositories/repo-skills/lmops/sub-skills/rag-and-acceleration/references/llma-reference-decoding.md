# LLMA reference-based decoding reference

LLMA is the lossless reference-based decoding workflow for cases where a model's output is expected to overlap with one or more references such as retrieved passages, prior turns, or known target text. It can accelerate decoding by reusing spans that appear in the references, while still verifying each copied token against the model before accepting it.

Use this reference when deciding whether LLMA is a fit for a RAG, multi-turn, or reference-overlap task. For a concrete toy check, run `scripts/llma_overlap_demo.py` with a small prompt/reference/target example.

## When LLMA fits

LLMA is a good fit when:

- the output has meaningful overlap with one or more references;
- the references are available during decoding;
- copied spans can be verified token by token without changing the final answer;
- preserving exact output matters more than approximate acceleration.

LLMA is a poor fit when the generation is mostly novel, when references are unrelated, or when the task is not expected to repeat wording from the source context. In that case, verification overhead can dominate and the speed benefit may disappear.

## Supported use cases

The inspected docs and code explicitly point to:

- retrieval-augmented generation;
- multi-turn conversations;
- summarization with source overlap;
- other tasks where references contain phrases the model would likely regenerate.

## CLI surface

The decoder entry point accepts the following concepts:

- `--model_path`: path to a converted LLaMA-family model.
- `--type`: `base` or `llma`.
- `--n`: trigger n-gram length for overlap detection.
- `--k`: copied block length parameter.
- `--append_docs`: prepend documents into the prompt.
- `--input_data_fn`: JSONL data file.
- `--forced_decoding`: benchmark mode that forces the target text rather than free generation.

The public examples use `type=base` for the baseline and `type=llma` for the accelerated pass. They also show `forced_decoding` for retrieval-augmented benchmarking where the target text is already known.

## Data shape

The decoder expects a JSONL file with records that include at least:

- `query`: the prompt or question.
- `docs`: a list of reference documents.
- `result.text`: optional target text used for forced-decoding or benchmark comparisons.

Each document is tokenized and truncated before decoding. In the inspected implementation, documents are shortened to a maximum of 768 tokens for the overlap cache, and the prompt builder can append the documents ahead of the query as `docs:\n...\nquery: ...\nanswer:`.

## Decoding behavior

The implementation follows this loop:

1. Build n-gram caches from the references and, when available, from the target text.
2. At each generation step, look for a recent n-gram in the generated output that matches a reference n-gram.
3. If a match appears, propose a copied block from the reference up to the `k` setting.
4. Run the model on the proposed block.
5. Accept only the prefix that matches the model's own output; if a mismatch occurs, shorten the cached state and continue.

This is why LLMA is lossless: copied tokens are still validated by the model before being committed. The method does not change the final text relative to the verified decode path.

## Important parameters

| Parameter | Effect |
| --- | --- |
| `n` | Smaller values trigger more overlap opportunities; larger values are stricter and may trigger less often. |
| `k` | Copied block size. Larger blocks can improve speed when overlaps are long, but they also increase verification work if the overlap is short. |
| `append_docs` | When enabled, documents are explicitly prepended to the prompt, which is useful for RAG-style overlap checks. |
| `forced_decoding` | Good for controlled benchmarking against a known target; not required for normal use. |
| `type=base` | Baseline one-token-at-a-time decode. |
| `type=llma` | LLMA overlap-aware decode. |

## Model and hardware notes

The public README recommends at least one NVIDIA V100 32GB GPU or better and converted LLaMA-family weights in Hugging Face format. A real run requires GPU memory and CUDA-capable PyTorch. The CPU-only demo script does not load a model and is only for overlap reasoning.

## Interpretation guidance

- If overlap is high, LLMA can often reduce the number of model calls.
- If overlap is low, the algorithm still verifies tokens but may not speed up meaningfully.
- LLMA is an exact acceleration method, not an approximate decoder.
- If a user wants faster serving for arbitrary generation, LLMA is the wrong tool; it is specialized for reference-heavy decoding.

## Safe demo route

Use `scripts/llma_overlap_demo.py` when you need a tiny example of how an overlap-triggered proposal is checked against a target sequence. The demo is CPU-only, uses whitespace tokenization, and avoids importing repository modules.
