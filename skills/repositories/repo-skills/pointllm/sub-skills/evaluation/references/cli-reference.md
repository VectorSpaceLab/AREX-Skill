# Evaluation CLI reference

These command templates use the installed-package wrapper bundled with the
inference sibling route. Run them in the prepared PointLLM environment; this
reference does not prescribe model loading or dataset setup. Run examples from
this evaluation sub-skill directory so `../../scripts/` resolves to the
bundled root launcher.

## Generate inference JSON

Objaverse open-vocabulary classification:

```bash
python ../../scripts/run_installed_cli.py eval_objaverse.py \
  --model_name MODEL \
  --task_type classification \
  --prompt_index 0
```

Use `--prompt_index 1` for the alternate classification prompt. Captioning:

```bash
python ../../scripts/run_installed_cli.py eval_objaverse.py \
  --model_name MODEL \
  --task_type captioning \
  --prompt_index 2
```

Useful generation overrides include `--data_path`, `--anno_path`, `--pointnum`
(default 8192), `--batch_size` (default 6), `--num_workers` (default 10), and
`--use_color`. `--start_eval --gpt_type MODEL` invokes the corresponding GPT
judge after generation or after loading an existing result file. Supported
`gpt_type` values are `gpt-3.5-turbo-0613`, `gpt-3.5-turbo-1106`,
`gpt-4-0613`, and `gpt-4-1106-preview`.

ModelNet40 close-set generation:

```bash
python ../../scripts/run_installed_cli.py eval_modelnet_cls.py \
  --model_name MODEL \
  --prompt_index 0
```

Use prompt index 1 for the alternate prompt. Relevant overrides are
`--split test`, `--subset_nums N` for a bounded run, `--batch_size` (default
30), `--num_workers` (default 20), and `--start_eval --gpt_type MODEL`.
Keep shuffle disabled.

## OpenAI judge

Set a credential only in the process environment after approval:

```bash
export OPENAI_API_KEY='[credential supplied out of band]'
python ../../scripts/run_installed_cli.py evaluator.py \
  --results_path RESULTS.json \
  --model_type gpt-4-0613 \
  --eval_type open-free-form-classification \
  --parallel --num_workers 15
```

Change `--eval_type` to `object-captioning` for Objaverse captions or
`modelnet-close-set-classification` for ModelNet40. The evaluator supports the
four model names above, derives the output file beside `RESULTS.json`, and
skips the run if that final file already exists. `--output_dir DIR` changes the
output location. The CLI parser defaults `parallel=True`; `--parallel` is a
store-true flag and there is no CLI `--no-parallel` switch. A single-thread run
requires the programmatic `start_evaluation(..., parallel=False)` interface.
Use a conservative worker count when rate limits or budget are unknown.

## Traditional caption metrics

```bash
python ../../scripts/run_installed_cli.py traditional_evaluator.py \
  --results_path CAPTION_RESULTS.json
```

Optionally pass `--output_dir DIR`. The default output is a sibling named
`*_evaluated_traditional.json`. This command may download WordNet and the
Sentence-BERT/SimCSE checkpoints. It does not provide a no-network mode.

## Local validation

```bash
python scripts/validate_results_json.py RESULTS.json --kind generation
python scripts/validate_results_json.py RESULTS.json --kind objaverse
python scripts/validate_results_json.py RESULTS.json --kind modelnet
python scripts/validate_results_json.py RESULTS.json --kind object-captioning
python scripts/validate_results_json.py RESULTS.json --kind traditional
```

The validator accepts `--kind auto` (the default), emits actionable errors,
and exits nonzero for malformed JSON or schema violations. It performs no
network, API, tokenizer, GPU, or model operations.
