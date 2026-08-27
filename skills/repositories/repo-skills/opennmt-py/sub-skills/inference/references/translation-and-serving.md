# Translation and serving reference

## Purpose

Use this reference when the task is to translate text, inspect scores or alignments, run the REST server, or choose between PyTorch and CTranslate2 inference paths. It is self-contained operating guidance distilled from OpenNMT-py's translation, server, inference-engine, and evaluation surfaces.

## Pick the surface

| Need | Surface | Notes |
| --- | --- | --- |
| Decode files, lists, or prompts | `onmt_translate` | Standard command-line path. |
| Score text or compute gold log-probs | `InferenceEnginePY` | Use the Python engine; CT2 scoring is not implemented. |
| Generate from a released CT2 model | `InferenceEngineCT2` | Use for released-model generation. |
| Expose a REST API | `onmt_server` or `TranslationServer` | Reads a JSON `model_config`. |
| Run LM-style benchmark prompts | Benchmark wrappers around `InferenceEnginePY` | Use for MMLU-style classification or Wikitext-style perplexity after model assets are supplied. |

## `onmt_translate` flags that matter most

### Decoding and search

- `--model`: one or more checkpoint paths. Required.
- `--src`: source input file. Required.
- `--output`: prediction output path.
- `--beam_size`: beam width.
- `--random_sampling_topk`, `--random_sampling_topp`, `--random_sampling_temp`: sampling-based generation.
- `--min_length`, `--max_length`, `--max_length_ratio`: length constraints.
- `--block_ngram_repeat`, `--ignore_when_blocking`: repetition blocking.
- `--replace_unk`, `--ban_unk_token`, `--phrase_table`: unknown-token handling.
- `--tgt_file_prefix`: prefix decoding from a provided target.

### Output and diagnostics

- `--tgt`: optional reference target file for scoring and gold alignment.
- `--with_score`: attach sentence scores.
- `--report_align`: emit word alignments.
- `--gold_align`: align source against gold target; requires `--report_align` and `--tgt`.
- `--attn_debug`: print attention matrices.
- `--align_debug`: print best alignments.
- `--dump_beam`: write beam traces as JSON.
- `--report_time`: log translation timing.
- `--verbose`: print predictions and scores per sentence.

### Data and device setup

- `--gpu`, `--gpu_ranks`, `--world_size`, `--parallel_mode`: device layout.
- `--batch_size`, `--batch_type`: sentence or token batching.
- `--precision`: `fp32`, `fp16`, or `int8` for the PyTorch path.
- `--model_task`: `seq2seq` or `lm`.
- `--transforms`, `--src_subword_model`, `--tgt_subword_model`, `--src_subword_vocab`: subword and tokenization routing.
- `--n_src_feats`, `--src_feats_defaults`: source-feature decoding.

Validation rules worth remembering:

- `gold_align` requires `report_align`, `tgt`, and no `replace_unk`.
- `InferenceEngineCT2` only supports single-process use; it rejects `world_size > 1`.
- `InferenceEngineCT2` does not implement scoring.

## Programmatic engines

### `InferenceEnginePY`

Use this when you need the full PyTorch translator behavior. Supported calls include:

- `infer_file()`
- `infer_list(src)`
- `score_file()`
- `score_list(src)`
- `terminate()`

Always call `terminate()` after use so spawned workers are stopped cleanly. `score_*` returns gold scores and, when requested, gold log-probabilities.

### `InferenceEngineCT2`

Use this for released-model inference through CTranslate2. Supported calls include:

- `infer_file()`
- `infer_list(src)`
- `terminate()`

For language models it constructs a `ctranslate2.Generator`; for seq2seq models it constructs a `ctranslate2.Translator`. It loads `src_subword_vocab` from the exported CT2 `vocabulary.json` when required.

## REST server configuration

`onmt_server` reads a JSON file with a top-level `models` list. A legacy single-model `model` alias is accepted, but the explicit `models` list is clearer.

Typical shape:

```json
{
  "models_root": "models",
  "models": [
    {
      "id": 100,
      "models": ["model.pt"],
      "timeout": 600,
      "on_timeout": "to_cpu",
      "load": true,
      "opt": {"gpu": 0, "beam_size": 5},
      "tokenizer": {"type": "sentencepiece", "model": "tokenizer.model"}
    }
  ]
}
```

Top-level keys:

- `models_root`: optional root for model artifacts; defaults to `./available_models` at runtime.
- `models`: required list of model entries.

Per-model entry:

| Field | Shape | Meaning |
| --- | --- | --- |
| `id` | int | Stable model id for `/translate`, `/clone_model`, and `/unload_model`. If omitted, the server auto-assigns one. |
| `models` | list[str] | Checkpoint paths. |
| `model` | str | Legacy alias for a single checkpoint path. |
| `model_root` | str | Per-entry model root used by `ServerModel`; avoid unless you also understand the startup precheck behavior. |
| `load` | bool | Load immediately at startup. |
| `timeout` | int | Seconds before the unload timer fires; negative disables the timer. |
| `on_timeout` | string | `to_cpu` or `unload`. |
| `opt` | object | Translate options passed through `onmt.opts.translate_opts`. |
| `tokenizer` | object | Tokenizer spec. |
| `features` | object | Source-feature routing for inference-time feature inference. |
| `preprocess` / `postprocess` | list[str] | Dotted import paths for custom hooks. |
| `custom_opt` | object | Extra values available to custom hooks. |
| `ct2_model` | str | CTranslate2 export directory. |
| `ct2_translator_args` | object | Passed to `ctranslate2.Translator`. |
| `ct2_translate_batch_args` | object | Passed to `translate_batch` / `generate_batch`. |

Important path note: the startup precheck checks model paths under the top-level `models_root`; `ServerModel` later uses `model_root` when loading models/tokenizers. The least surprising production pattern is to keep a single `models_root` and omit per-entry `model_root` unless you have tested the exact config.

## Tokenizers and features

The `tokenizer` entry can be either a shared tokenizer or a side-specific pair:

- shared SentencePiece: `{"type": "sentencepiece", "model": "tokenizer.model"}`
- shared pyonmttok: `{"type": "pyonmttok", "mode": "aggressive", "params": {...}}`
- side-specific: `{"src": {...}, "tgt": {...}}`

Rules:

- SentencePiece requires a `model` path.
- pyonmttok requires a `mode` key and a `params` object.
- Any tokenizer param key ending in `path` is resolved relative to the model root and must exist.
- If you need alignment output, use reversible tokenization consistently on both sides.

When `features` is present, the server expects:

- `n_src_feats`: integer count.
- `src_feats_defaults`: feature defaults separated by `￨`.
- `reversible_tokenization`: `joiner` or `spacer`.

The feature-default count must match `n_src_feats`.

## REST endpoints

The server exposes these endpoints under the configured `url_root`:

- `GET /health`
- `GET /models`
- `POST /translate`
- `POST /clone_model/<model_id>`
- `GET /unload_model/<model_id>`
- `GET /to_cpu/<model_id>`
- `GET /to_gpu/<model_id>`

`/translate` accepts a list such as `[{"id": 100, "src": "..."}]` and returns grouped `n_best` results with `src`, `tgt`, `pred_score`, and optional `align` / `align_score` fields.

## CTranslate2-specific notes

`CTranslate2Translator.convert_onmt_to_ct2_opts()` enforces consistency between CT2 arguments and OpenNMT translate options:

- `inter_threads` defaults to `1`.
- `intra_threads` defaults to `torch.get_num_threads()`.
- `compute_type` defaults to `default`.
- `device` must match the OpenNMT `gpu` choice.
- `beam_size`, `max_batch_size`, `num_hypotheses`, `max_decoding_length`, and `min_decoding_length` must agree with the OpenNMT options when specified in both places.

## Benchmark-style evaluation contracts

MMLU-style evaluation builds few-shot prompts, normalizes prompt newlines with a sentinel token, calls `InferenceEnginePY.infer_list()`, and scores next-token classification answers.

Wikitext-style evaluation detokenizes a raw corpus, chunks it into rolling context windows, and calls `InferenceEnginePY.score_list()` with gold log-probability output. CT2 is not a scoring substitute for this route because CT2 scoring is not implemented in this package.

For chat or prompt routers, use the same tokenizer model for prompt-length accounting and keep pruning rules aligned with the model's actual subword segmentation.
