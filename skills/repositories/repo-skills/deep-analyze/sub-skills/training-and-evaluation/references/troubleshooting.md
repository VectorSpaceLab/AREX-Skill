# Training and evaluation troubleshooting

Use this guide before retrying a failed DeepAnalyze training or benchmark command. Most failures are caused by placeholders, missing data, incompatible environments, or heavy GPU memory requirements.

## Placeholder paths and unsafe launches

Symptoms:

- Command contains `PATH_TO_MODEL`, `PATH_TO_SAVE_MODEL`, `PATH_TO_DataScience-Instruct`, `path_to_DeepAnalyze-8B`, `YOUR_API_KEY`, or similar placeholders.
- Output path is the same as an input checkpoint.
- A benchmark script uses a private or stale model endpoint value.

Fix:

1. Stop before execution.
2. Ask the user for real model, data, endpoint, key, and output values.
3. Render the plan with `../scripts/render_training_command.py` or `../scripts/benchmark_command_builder.py`.
4. Use `--check-files` where local files should exist.
5. Make overwrite/resume behavior explicit.

## Missing DataScience-Instruct-500K data

Symptoms:

- SFT command cannot open JSON data files under `reasoning/` or `interation/`.
- RL command cannot open `qa.parquet`, `datatask.parquet`, `reseach.parquet`, or workspace data.
- RL environment raises `workspace not found`.

Fix:

- Download `DataScience-Instruct-500K` and set `DATA_DIR` to its root.
- Preserve the official directory spellings: `interation` and `reseach.parquet` unless the user's dataset version differs.
- Unzip `RL/data.zip` so that `DATA_DIR/RL/data/` exists before RL.
- For RL items with `workspace_id`, verify the nested workspace exists below `DATA_DIR/RL/data/<task>/<workspace_id>/`.

## Special-token and tokenizer issues

Symptoms:

- Model does not emit or recognize `<Analyze>`, `<Code>`, `<Execute>`, or `<Answer>` tags reliably.
- SFT fails after resizing embeddings or loading a tokenizer.
- RL rewards return `-1.0` for missing tags.

Fix:

- If starting from `DeepSeek-R1-0528-Qwen3-8B`, run special-token preprocessing to a new save path before SFT.
- If starting from `DeepAnalyze-8B`, do not add tags again unless the tokenizer is proven missing them.
- Verify the tokenizer/model pair are from the same checkpoint directory.

## Training environment conflicts

Symptoms:

- `swift` command missing.
- SkyRL install fails because Python version is not 3.12.
- vLLM, ms-swift, SkyRL, Ray, or Transformers pin incompatible dependencies.

Fix:

- Use separate environments for SFT, RL, and serving/evaluation.
- Install DeepAnalyze's forked `ms-swift` editable in the SFT environment.
- Install SkyRL editable in a Python 3.12 RL environment.
- Avoid upgrading core packages after editable installs unless you rerun import checks.

## CUDA, NCCL, DeepSpeed, FlashAttention, and Liger failures

Symptoms:

- CUDA device not visible or invalid device ordinal.
- NCCL all-reduce/weight-sync failures.
- DeepSpeed Zero-3 initialization errors.
- FlashAttention import/build/runtime error.
- Liger kernel import or shape error.

Fix:

1. Confirm `CUDA_VISIBLE_DEVICES`, `NPROC_PER_NODE`, and actual `nvidia-smi` GPU count agree.
2. Use a free `MASTER_PORT`; change it if another distributed job is running.
3. Match PyTorch/CUDA/FlashAttention versions for the driver and GPU architecture.
4. If Liger fails, retry a small SFT smoke with `--use_liger_kernel false` only after the user accepts deviating from the official recipe.
5. If FlashAttention fails, retry with a supported attention implementation only as an explicit diagnostic; record the deviation.
6. For NCCL issues, set diagnostics such as `NCCL_DEBUG=INFO` and check multi-node variables (`NNODES`, `NODE_RANK`, `MASTER_ADDR`) when applicable.

## Long-context memory and throughput

Symptoms:

- Out of memory near sequence length 8192 or 32768.
- vLLM/RL generator OOMs before training starts.
- Training is extremely slow or hangs at data packing.

Fix:

- Reduce per-device batch size first, then adjust gradient accumulation to keep effective batch size if needed.
- Verify `max_length=32768`, `generator.max_input_length=32768`, and `max_generate_length=32768` are truly required for the experiment.
- For RL, lower `generator.gpu_memory_utilization`, `n_samples_per_prompt`, or batch sizes if accepted by the user.
- Use fewer concurrent benchmark tasks when GPU memory is shared.
- Keep long-context training off GPUs already serving vLLM endpoints.

## Ray, Hydra, and SkyRL DeepAnalyzeEnv issues

Symptoms:

- Ray reports a stale cluster, worker crash, or head-node scheduling problem.
- Hydra rejects an override or cannot find the entrypoint module.
- `DeepAnalyzeEnv` asserts missing `reward_spec` or `data`.
- LLM judgement returns errors or zero reward.

Fix:

- Start from the `deepanalyze/SkyRL/skyrl-train` working directory for the RL entrypoint.
- Clear stale Ray state only after confirming no other user jobs depend on it.
- Keep Hydra list values quoted exactly in the rendered command.
- Confirm RL parquet rows contain `reward_spec`, `data`, and any expected `workspace_id` fields.
- Configure the OpenAI-compatible judgement client if the reward function uses LLM judgement: API key or accepted token, base URL, and model name.

## Benchmark output caching and resume

DABStep-Research:

- Existing `<task_id>.jsonl` files are treated as completed. Remove or move bad files before rerun.
- Missing `<Answer>` blocks produce error records or failed attempts; inspect reasoning traces.

DS-1000:

- Inference resume counts existing lines in `data/<model_slug>-answers.jsonl`.
- Evaluation reads `data/<model_slug>-answers.jsonl` using the slug passed to `test_ds1000.py --model`.
- If inference used a path-derived or default slug and evaluation uses another value, regenerate or rename consistently.

DSBench:

- Data-analysis skips existing per-sample JSON outputs under `save_process/<model>/`.
- Data-modeling skips existing per-task CSV outputs under `output_model/<model>/`.
- Remove only the failed task's stale output; do not delete whole benchmark runs unless requested.

TableQA:

- Prediction JSON, evaluation JSON, logs, and `.temp` files can indicate partial progress.
- The shell loop may reference `tests_our`; use `tests` if that is the actual directory or pass the correct directory to the command builder.
- LLM and combined evaluation need an evaluator model path or API model identifier.

## Missing model endpoint

Symptoms:

- Connection refused at `localhost:8000` or `/v1/chat/completions`.
- DABStep, DSBench, or LLM evaluator reports OpenAI client connection errors.
- A benchmark runner initializes vLLM but no model path exists.

Fix:

- Route to `model-serving` to select and launch the model server.
- Distinguish the vLLM model endpoint from the DeepAnalyze API server and frontend ports.
- Verify `/v1/models` or a minimal chat completion before starting a long benchmark.
- Do not embed API keys in scripts or committed files; pass them through environment variables or local config ignored by version control.

## Benchmark data and dependency gaps

- DS-1000 needs a benchmark environment that can execute generated code, including plotting and selected ML/scientific packages.
- DSBench data-analysis requires processed finance/modeloff-style data; data-modeling requires processed Kaggle-style data and task workspaces.
- TableQA task scripts require their table datasets under the expected `data/<task>/` paths.
- LLM-as-judge evaluators require OpenAI-compatible client dependencies and endpoint configuration.
