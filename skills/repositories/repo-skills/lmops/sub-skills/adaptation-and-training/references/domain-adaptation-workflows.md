# Domain adaptation workflows

This reference covers two related families:

- AdaptLLM-style raw domain text conversion into reading-comprehension form.
- Domain benchmark inference planning for AdaptLLM and Instruction-Pre-Training checkpoints.

## Choose the right path

| Need | Use | Notes |
| --- | --- | --- |
| Turn raw domain text into a compact reading-comprehension fixture | `scripts/raw_to_reading_comprehension.py` | Safe, CPU-only, self-contained. |
| Prepare a paper-faithful large corpus conversion | Human-run AdaptLLM workflow in the original project | Not bundled here; use this skill only for planning and fixture support. |
| Evaluate a domain checkpoint on biomedicine, finance, or law tasks | Domain inference planning | Requires the right model family, tokenizer behavior, and GPU budget. |

## AdaptLLM conversion concepts

AdaptLLM frames domain adaptation as converting raw text into reading-comprehension style training material.

### Typical source shape

- Raw documents are plain text files.
- The first line often behaves like a title.
- The remaining text is the context to be rewritten into reading-comprehension form.
- The paper workflow mines several task families such as classification, common-reasoning, paraphrase, word-to-text, summarize, and text-completion patterns.

### Safe distilled helper

Use the bundled script to exercise the core idea on a tiny fixture:

```bash
python scripts/raw_to_reading_comprehension.py \
  --input-dir ./sample-raw-texts \
  --output-dir ./sample-read-compre \
  --domain-name biomedicine
```

The helper is intentionally small:

- It does not import repository code.
- It does not download models.
- It can create fixture input text if requested.
- It emits a stable, human-readable reading-comprehension rendering plus a compact JSON summary.

### What to preserve when adapting the idea

- Keep the raw title/context split explicit.
- Keep the domain label visible in the output metadata.
- Avoid assuming every document already has a title line.
- Treat long-document truncation as a planning concern, not an automatic promise.
- Be conservative about generated question diversity; the helper favors traceability over paper-scale richness.

## Domain benchmark inference planning

AdaptLLM and Instruction-Pre-Training use a domain benchmark recipe with these important switches:

- `DOMAIN`: one of `biomedicine`, `finance`, or `law`.
- `MODEL`: a supported domain checkpoint name.
- `MODEL_PARALLEL`: whether the checkpoint requires model sharding.
- `N_GPU`: the number of GPUs to reserve.
- `add_bos_token`: `false` for AdaptLLM-style checkpoints and `true` for instruction-pretrained checkpoints.

### Planning checklist

1. Match the checkpoint family to the tokenizer convention.
2. Choose a single-GPU or model-parallel plan before touching the launcher.
3. Confirm whether the checkpoint is a base model or a chat model.
4. Confirm the task family is one of the supported domain benchmarks.
5. Reserve cache and output locations before starting inference.

### Common failure patterns

- The model does not fit on one GPU.
- The wrong `add_bos_token` setting changes the prompt boundary.
- A chat model is sent through a benchmark recipe intended for base models.
- A checkpoint path exists but points to the wrong family or tokenization scheme.
- The inference cache or output directory is missing or unwritable.

## What not to do

- Do not treat the safe helper as a replacement for paper-scale conversion quality.
- Do not use this sub-skill for MiniLLM, DPKD, Tuna, or VeRL-style post-training.
- Do not hide GPU, tokenizer, or model-family requirements.
