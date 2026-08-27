# Workflows

This sub-skill covers the Self-Instruct-style instruction-generation loop used by Stanford Alpaca. The live workflow is intentionally credential-gated; the bundled scripts are offline-only and safe for prompt/debug work.

## 1) Offline prompt debugging
Use the bundled renderer when you want to confirm that seed-task records are formatted exactly like the generator expects.

```bash
python scripts/render_instruction_prompt.py --self-check
python scripts/render_instruction_prompt.py --seed-tasks-path ./tiny_seed_tasks.jsonl --count 3
```

What to look for:
- The prompt starts with the bundled template text.
- Each example is numbered and rendered as `Instruction`, `Input`, and `Output` blocks.
- Empty inputs become `<noinput>`.
- The prompt ends with the next `Instruction:` slot.

## 2) Offline completion parsing
Use the bundled parser when you already have saved completion text or a JSON payload and want to see which candidates survive the source filters.

```bash
python scripts/parse_openai_response.py --self-check
python scripts/parse_openai_response.py --completion-path ./saved_response.json --num-prompt-instructions 3
```

The parser mirrors the source post-processing rules:
- split on `###`
- drop the last chunk when the finish reason is `length`
- parse numbered `Instruction` / `Input` / `Output` triples
- filter short or very long instructions
- reject banned keywords, punctuation starts, non-ASCII starts, and `Write a program...`

## 3) Live generation workflow
Only use the live path when credentials and network access are available.

Prerequisites:
- `OPENAI_API_KEY`
- optional `OPENAI_ORG`
- outbound network access
- a legacy OpenAI client that still exposes the completion surface used by the source code

Generation settings from the source function:

| Parameter | Default | Meaning |
| --- | --- | --- |
| `output_dir` | `./` | Destination for `regen.json` and other generated artifacts. |
| `seed_tasks_path` | `./seed_tasks.jsonl` | Seed-task JSONL file. |
| `num_instructions_to_generate` | `100` | Target number of accepted instructions. |
| `model_name` | `text-davinci-003` | Legacy completion model used by the source workflow. |
| `num_prompt_instructions` | `3` | Number of seed examples sampled into each prompt. |
| `request_batch_size` | `5` | Number of prompts sent per OpenAI request. |
| `temperature` | `1.0` | Sampling temperature. |
| `top_p` | `1.0` | Nucleus sampling parameter. |
| `num_cpus` | `16` | Parallel workers for ROUGE-L deduplication. |

Internal decoding settings used by the generator:
- `OpenAIDecodingArguments(temperature=temperature, n=1, max_tokens=3072, top_p=top_p, stop=["\n20", "20.", "20."])`
- the OpenAI helper also adds `logit_bias={"50256": -100}` to suppress end-of-text generation

## 4) `regen.json` resume behavior
The live generator treats `regen.json` as the resume ledger.

- If `output_dir/regen.json` exists, it is loaded before generation starts.
- Accepted machine-generated records are appended to that list.
- The file is rewritten after each request batch.
- The progress bar starts from the number of already accepted records.

Best practice:
- If you change the prompt template, filters, seed set, or dedup policy, use a new output directory instead of resuming an older `regen.json`.

## 5) Typical analysis flow
1. Render a prompt from a tiny fixture.
2. Inspect one saved completion text.
3. Check which records are filtered out and why.
4. Only then decide whether a live API run is worth the cost.
