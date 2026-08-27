# DeepAnalyze benchmark playgrounds

This reference routes evaluation requests through DeepAnalyze's bundled playgrounds. The playgrounds are useful but not turnkey: they assume benchmark data has been downloaded, model serving or vLLM dependencies are installed, and several scripts contain placeholders. Prefer the dry-run planner `../scripts/benchmark_command_builder.py` before any execution.

## Common evaluation prerequisites

- A model checkpoint or model endpoint. If the user needs a vLLM launch plan, route to `model-serving` first.
- Benchmark-specific data in the expected relative directory.
- Clear output directory and resume policy.
- Enough GPU memory for inference when the playground loads a local model with vLLM.
- A sandbox for code-execution benchmarks; DS-1000 and agentic report benchmarks execute generated Python or evaluate generated artifacts.
- An evaluator model endpoint/key for LLM-as-judge modes.

Use stable model slugs for output files. Avoid putting raw filesystem model paths into output file names when a script also expects the slug later.

## Route summary

| Goal | Playground route | Main input | Main output | Resume/cache behavior |
| --- | --- | --- | --- | --- |
| Data-analysis report generation | DABStep-Research | `dabstep_research.jsonl` plus context files | one JSONL record per task under a run directory | skips task output files that already exist |
| Data-science code generation | DS-1000 | `data/ds1000.jsonl.gz` or equivalent dataset | `data/<model_slug>-answers.jsonl`, then result text/logs | inference can count existing answer lines with `--resume`; evaluation reads by slug |
| Realistic analysis/modeling agents | DSBench | processed data zips for data-analysis or data-modeling subtasks | per-task process/model outputs, then result summaries | skips existing process/model outputs |
| Table QA tasks | TableQA | table task datasets under `data/<task>/` | prediction JSON, eval JSON, logs | inference temp files and final result files support manual resume checks |

## DABStep-Research

Purpose: evaluate a DeepAnalyze-style agent on data-report tasks. Each task includes an instruction, a checklist, a type, and a list of files such as CSV, JSON, Markdown, and documentation files. The runner builds a prompt with file metadata, calls a DeepAnalyze vLLM-compatible agent, extracts the last `<Answer>` block, and writes one JSONL file per task.

Expected configurable values:

- `model_id`: served model name or local checkpoint identifier used by the agent.
- `api_url`: OpenAI-compatible chat-completions URL, commonly `http://localhost:8000/v1/chat/completions` for a vLLM server.
- `task_jsonl`: DABStep task list, default `dabstep_research.jsonl`.
- `context_dir`: directory containing task context files.
- `output_dir`: run directory such as `runs/deepanalyze`.
- `num_processes`: multiprocessing width.

Output record fields:

```text
task_id
agent_answer
reasoning_trace
question
checklist
type
```

Operational notes:

- The generation helper uses `<Code>` and `<Execute>` loops and stops after a bounded number of rounds.
- Completed tasks are detected by existing `<task_id>.jsonl` files in the output directory.
- The evaluator script uses an OpenAI-compatible client and must be edited or wrapped with real `api_key`, `base_url`, and evaluator model. Do not copy hardcoded placeholders into a command plan.
- If no model endpoint is running, route to `model-serving` before trying DABStep.

Dry-run plan:

```bash
python skills/disco/deep-analyze/sub-skills/training-and-evaluation/scripts/benchmark_command_builder.py \
  dabstep \
  --model-id DeepAnalyze-8B \
  --api-url http://localhost:8000/v1/chat/completions \
  --output-dir runs/deepanalyze
```

## DS-1000

Purpose: evaluate data-science code completion across 1000 tasks. The inference runner loads a vLLM model, generates code batches, and writes answers to `data/<model_slug>-answers.jsonl`. The tester executes generated code in isolated worker processes and writes summaries under `results/`.

Required data:

- `data/ds1000.jsonl.gz` in the simplified format, or a downloaded equivalent converted to that path.
- Environment dependencies from the DS-1000 environment file plus `datasets` and `tqdm` if loading from Hugging Face.

Recommended two-step command shape:

```bash
python run_deepanalyze.py --model "$MODEL_PATH" --model_name "$MODEL_SLUG" --resume
python test_ds1000.py --model "$MODEL_SLUG"
```

Important slug rule:

- Inference writes answers using `--model_name`; evaluation reads answers using `--model`.
- If `--model` is a filesystem path during evaluation, the tester will look for an answer file derived from that path and may not find the inference output. Always pass a stable slug such as `DeepAnalyze-8B-custom` to both `--model_name` and evaluation `--model`.

Execution safety:

- The tester executes generated code. Use an isolated benchmark environment.
- TensorFlow logging is silenced and CUDA is disabled inside the tester, but generated code can still use filesystem operations allowed by the sandbox.
- Some tasks are stateful; independent worker processes are intentional.

Dry-run plan:

```bash
python skills/disco/deep-analyze/sub-skills/training-and-evaluation/scripts/benchmark_command_builder.py \
  ds1000 \
  --model-path "$MODEL_PATH" \
  --model-slug DeepAnalyze-8B-custom \
  --resume
```

## DSBench

Purpose: evaluate data-science agents on realistic data-analysis and data-modeling tasks.

Data-analysis route:

1. Download and unzip the processed data-analysis archive into the expected `data/` directory.
2. Configure the model endpoint, model name, and any API client settings in the runner or a local wrapper.
3. Run inference to produce per-task JSON lines under `save_process/<model_name>/`.
4. Run answer computation and result display:

```bash
python compute_answer.py
python show_result.py
```

Data-modeling route:

1. Download and unzip the processed data-modeling archive.
2. Configure working directory, save path, model slug, and DeepAnalyze agent model path in a local wrapper or the runner.
3. Run inference to create `submission.csv` for each competition and copy outputs under `output_model/<model>/`.
4. Score and summarize:

```bash
python score4each_com.py
python show_result.py
```

Operational notes:

- Data-analysis skips a sample when its output JSON already exists.
- Data-modeling skips a competition when its output CSV already exists.
- Official runner samples include placeholders and hardcoded model/endpoint values; replace them in a private wrapper or edited working copy before execution.
- Data-modeling can run for up to an hour per task and writes/removes `submission.csv` in each task workspace.

Dry-run plans:

```bash
python skills/disco/deep-analyze/sub-skills/training-and-evaluation/scripts/benchmark_command_builder.py \
  dsbench-analysis \
  --model-slug DeepAnalyze-8B \
  --api-base http://localhost:8000/v1

python skills/disco/deep-analyze/sub-skills/training-and-evaluation/scripts/benchmark_command_builder.py \
  dsbench-modeling \
  --model-slug DeepAnalyze-8B \
  --model-path "$MODEL_PATH"
```

## TableQA

Purpose: evaluate DeepAnalyze on table-question-answering datasets with standard exact-match, LLM-only, or combined evaluation modes.

Supported task names from the official loop:

```text
ottqa tatqa finqa hybridqa multihiertt tablebench hitab wikitq fetaqa aitqa feverous totto wikisql tabfact
```

Core variables:

- `MODEL_PATH`: local model path used by vLLM inference.
- `MODEL_NAME`: output slug under `results/`.
- `TRAIN_TYPE`: metadata suffix such as `sft`, `grpo`, or `ppo`.
- `MODEL_SIZE`: metadata suffix such as `8b`.
- `TENSOR_PARALLEL_SIZE`: must match the model and GPU allocation.
- `BATCH_SIZE` and `MAX_TOKENS`: inference throughput and output length controls.
- `EVAL_MODE`: `standard`, `llm`, or `combined`.
- `EVAL_MODEL_PATH`: required for `llm` and `combined`; may be a local evaluator checkpoint or API model identifier accepted by the evaluator helper.
- `LLM_EVAL_BATCH_SIZE`: batch/concurrency for LLM evaluation.

Command shape for one task:

```bash
python tests/<task>.py \
  --model_path "$MODEL_PATH" \
  --output_file "results/$MODEL_NAME/<task>/<task>_${MODEL_SIZE}_${TRAIN_TYPE}.json" \
  --log_file "results/$MODEL_NAME/<task>/logs/<task>_${MODEL_SIZE}_${TRAIN_TYPE}_infer.log" \
  --base_path "$(pwd)" \
  --tensor_parallel_size "$TENSOR_PARALLEL_SIZE" \
  --batch_size "$BATCH_SIZE" \
  --max_tokens "$MAX_TOKENS" \
  --temperature 0.0

python tests/eval/<task>_eval.py \
  --results_file "results/$MODEL_NAME/<task>/<task>_${MODEL_SIZE}_${TRAIN_TYPE}.json" \
  --output_file "results/$MODEL_NAME/<task>/<task>_${MODEL_SIZE}_${TRAIN_TYPE}_eval_results.json" \
  --base_path "$(pwd)"
```

For `llm` mode use `tests/llm_eval/<task>_eval.py` with `--model_path`, `--log_file`, `--batch_size`, and `--tensor_parallel_size`. For `combined`, use `tests/llm_eval/<task>_combined_eval.py` and add `--evaluation_mode combined`.

Path caution:

- The top-level shell loop in the playground refers to a `tests_our` directory, while the inspected tree contains `tests`. Verify the actual directory before launch or use the command builder's `--tests-dir` option.

Dry-run plan:

```bash
python skills/disco/deep-analyze/sub-skills/training-and-evaluation/scripts/benchmark_command_builder.py \
  tableqa \
  --model-path "$MODEL_PATH" \
  --model-slug DeepAnalyze-8B \
  --tasks wikitq,tabfact \
  --eval-mode combined \
  --eval-model-path "$EVAL_MODEL_PATH"
```
