# EMMA-mini and MMK12 workflows

This reference collects the Skywork-specific command surfaces for EMMA-mini generation and MMK12 generation/scoring.

## EMMA-mini

Source files:

- `eval/EMMA/generate_response.py`
- `eval/EMMA/data_utils.py`
- `eval/EMMA/configs/gpt.yaml`
- `eval/EMMA/run_skywork.sh`
- `eval/EMMA/evaluation/*.py`

### Command surface

`generate_response.py` accepts:

- `--dataset_name` default `luckychao/EMMA`
- `--subject` one or more subject names
- `--split` default `test`
- `--strategy` `CoT` or `Direct`
- `--config_path` for the YAML prompt template
- `--output_path` for the result JSON file
- `--save_every` for incremental saves
- `--rerun` to force regeneration
- either a remote model through `--model` and `--api_key`, or a local model through `--model_path`
- remote model choices in the source script: `chatgpt-4o-latest`, `claude-3-5-sonnet-latest`, `gemini-2.0-flash-exp`, and `gemini-2.0-flash-thinking-exp-1219`
- `--max_tokens` and `--temperature`

### Important behavior

- The script concatenates the selected subject datasets before generation.
- `build_query()` chooses the prompt template from the YAML file and appends the CoT/Direct instruction.
- `verify_response()` treats blank outputs and strings containing `Response Error` as invalid.
- The output file is a JSON object keyed by problem id.
- The evaluation helpers read that JSON and write result and accuracy companions.
- The source Skywork shell recipe uses `--max_tokens 64000`, `--temperature 0.7`, and `--save_every 3` for the open-source EMMA run.

### Local-model branch

The local branch chooses a model adapter based on the `model_path` string:

- `llava` -> LLaVA adapter
- `qwen2.5-vl` -> Qwen2.5-VL adapter
- `internvl` -> InternVL adapter
- `skywork` or `r1v3` -> Skywork adapter

Treat those adapters as workflow evidence, not as a promise that every checkpoint will run on the current host.

## MMK12

Source files:

- `eval/MMK12/evaluate.py`
- `eval/MMK12/calculate_score.py`
- `eval/MMK12/launch_skywork_r1v3.sh`

### Command surface

The generation script expects:

- `--datasets` as a comma-separated list, default `MMK12`
- `--out-dir` for the output JSON directory
- `--seed`

The scoring script expects:

- `--output_dir`
- `--output_file`
- `--response_label`
- `--number`
- `--output_label`

### Important behavior

- The generation script loads `FanqingM/MMK12`.
- It sends messages to a local OpenAI-compatible client and expects the served model name `r1v3-alpha`.
- The scoring script first prefers `<answer>...</answer>` content and otherwise falls back to the last boxed answer.
- Final judge output must reduce to `Yes` or `No`.

## Evaluation-specific guidance

- Keep the model server, client base URL, and served model name aligned.
- Keep credentials in the environment, not in bundled runtime files.
- Lower the worker count if the local endpoint becomes unstable.
- Use `score_boxed_answers.py` for rule-based answer normalization when you want a safe helper instead of the original repository scripts.
