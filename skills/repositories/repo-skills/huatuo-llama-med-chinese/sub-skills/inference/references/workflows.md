# Inference workflows

This reference distills the repository's inference behavior into reusable operating guidance. It is not a request to inspect or execute the original source files; use the bundled command builder for safe command construction.

## Workflow selection

| Workflow | Use when | Inference entrypoint shape | Template default | Notes |
| --- | --- | --- | --- | --- |
| `medical-qa` | The user has a JSONL file of Chinese medical QA prompts and wants model-vs-gold output. | Batch/file runner with `--instruct_dir`. | `med_template` for LLaMA/Alpaca; `bloom_deploy` for Bloom/Huozi. | Requires explicit base model, LoRA adapter, and JSONL path. |
| `literature-single` | The user wants one-shot liver-cancer/literature-style QA examples. | Literature runner with `--single_or_multi single`. | `literature_template`. | Uses built-in single-turn prompts in the source workflow rather than an input file. |
| `literature-multi` | The user wants an interactive multi-turn literature conversation. | Literature runner with `--single_or_multi multi`. | `literature_template`. | The loop collects five user inputs and appends `<user>:` / `<bot>:` history. |
| `gradio` | The user wants an interactive web UI around the medical QA model. | Gradio runner with `server_name` and `share_gradio`. | `med_template` for LLaMA/Alpaca; `bloom_deploy` for Bloom/Huozi. | Use conservative serving defaults unless exposure is explicitly authorized. |

## Shared prerequisites

Real inference is outside the safe dry-run scope and requires all of the following:

- Python 3.9+ with compatible `torch`, `transformers`, `peft`, `sentencepiece`, and, for serving, `gradio`.
- A base model from the same family used by the adapter. Repository evidence names LLaMA-7B, Chinese Alpaca, Bloom/BloomZ-7B, and Huozi-style Bloom-derived models.
- A LoRA adapter directory or Hugging Face adapter id matching the base model. Local adapter directories should contain `adapter_config.json` and `adapter_model.bin`.
- A compatible CUDA installation for the medical QA and literature CLI runners. Those runners set `device = "cuda"` only when CUDA is available and can otherwise fail before generation.
- Enough GPU memory for 7B-scale half-precision model loading. The README's training reference mentions A100 usage and 24 GB-class GPUs as a practical lower bound for adjusted workloads; inference may still require careful memory management.
- No automatic trust in model output: medical generations are research artifacts and are not clinical advice.

## Prompt template selection

| Model/workflow context | Use this template | Response split marker | Why it matters |
| --- | --- | --- | --- |
| LLaMA/Chinese-Alpaca medical QA | `med_template` | `### 回答:` | Matches the medical knowledge QA prompt format. |
| Bloom/Huozi medical QA or deployment | `bloom_deploy` | `### 回答：` | Uses a similar Chinese medical prompt but a full-width colon in the response marker. |
| Literature single-turn or multi-turn LoRA workflow | `literature_template` | `### 回复:` | Matches the literature runner's `<user>:`/`<bot>:` style prompts and split marker. |
| Legacy raw LLaMA / default Alpaca comparisons | `ori_template` / `alpaca` only if supplied by the runtime project | varies | The comparative shell comments mention these legacy templates, but they are not part of the observed template set. Validate before use. |

If the output cannot be split or starts echoing the whole prompt, suspect a template/adapter mismatch before blaming model quality. Route detailed template JSON editing or input-schema conversion to `prompt-data-formats`.

## Medical QA batch inference

The medical QA workflow loads a tokenizer and causal LM from `--base_model`, optionally composes a PEFT LoRA adapter from `--lora_weights`, renders each JSONL record's `instruction`, and prints a comparison block containing the instruction, the gold `output`, and the generated response.

Distilled command shape:

```bash
python infer.py \
  --base_model "$BASE_MODEL" \
  --lora_weights "$LORA_DIR_OR_ID" \
  --use_lora True \
  --instruct_dir "$INFER_JSONL" \
  --prompt_template med_template
```

Important behavior:

- `--instruct_dir` is a JSON Lines file. Each line must be a JSON object with at least `instruction` and `output`; `input` may exist but the source inference loop does not pass it into generation.
- If `--instruct_dir` is empty, the runner uses a small set of built-in Chinese medical questions.
- `--use_lora False` runs the base model without the medical adapter and is useful only for baseline comparisons.

Generation defaults in this workflow:

- `temperature=0.1`
- `top_p=0.75`
- `top_k=40`
- `num_beams=4`
- `max_new_tokens=256`

## Literature single-turn inference

The single-turn literature workflow composes the literature LoRA adapter and runs a fixed list of liver-cancer/literature-style questions. Each question is prefixed with `<user>:` before prompt rendering.

Distilled command shape:

```bash
python infer_literature.py \
  --base_model "$BASE_MODEL" \
  --lora_weights "$LITERATURE_LORA_DIR_OR_ID" \
  --single_or_multi single \
  --use_lora True \
  --prompt_template literature_template
```

Use this workflow for quick qualitative checks of the literature adapter. Do not use a medical-knowledge adapter with the literature template unless the user is deliberately testing a mismatch.

## Literature multi-turn inference

The multi-turn literature workflow is interactive. It loops for five turns, reads user input from stdin, appends `<user>: ...` to the accumulated history, generates a response, removes newlines, prints `Response: ...`, and appends ` <bot>: ...` back into the history for the next turn.

Distilled command shape:

```bash
python infer_literature.py \
  --base_model "$BASE_MODEL" \
  --lora_weights "$LITERATURE_LORA_DIR_OR_ID" \
  --single_or_multi multi \
  --use_lora True \
  --prompt_template literature_template
```

Difficult case to handle carefully: if a user asks for literature multi-turn inference but supplies `med_template`, switch to `literature_template` unless they explicitly want a mismatch experiment. The `med_template` response marker is `### 回答:`, while the literature workflow expects `### 回复:`; a wrong split marker can produce prompt echoes, split errors, or empty responses.

## Gradio-style serving

The serving workflow launches a Gradio interface around the same `evaluate()` pattern. It accepts instruction/input text plus generation controls in the browser.

Distilled command shape with conservative serving settings:

```bash
python generate.py \
  --base_model "$BASE_MODEL" \
  --lora_weights "$LORA_DIR_OR_ID" \
  --prompt_template med_template \
  --server_name 127.0.0.1 \
  --share_gradio False
```

Source behavior to account for:

- The source default server name is `0.0.0.0`, which binds to all interfaces.
- The source default `share_gradio=True` can create an externally reachable share link.
- Use `127.0.0.1` and `False` unless the user explicitly authorizes exposure.
- `generate.py` defines CPU and MPS fallbacks, unlike the batch/literature runners, but 7B-scale CPU inference is usually impractical.

Generation defaults in the serving workflow:

- `temperature=0.1`
- `top_p=0.75`
- `top_k=40`
- `num_beams=4`
- `max_new_tokens=128` by default, adjustable in the UI up to 2000.

## Comparative recipe captured as reference-only

The repository's comparative test recipe runs three expensive generations and writes separate output files:

1. Raw/base LLaMA with LoRA disabled and a raw-template-style prompt.
2. Default Alpaca LoRA with an Alpaca-style prompt.
3. Medical LoRA with `med_template`.

Treat this as a manual evaluation pattern, not as a default smoke test. It requires multiple large model loads, matching templates that may not all be present, a writable output directory, and explicit GPU/model-weight authorization. For a safe plan, build each command separately with `scripts/build_inference_command.py` and ask the user before any real execution.
