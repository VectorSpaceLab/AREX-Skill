# Evaluation troubleshooting

This file covers failures in the Skywork evaluation stack: VLMEvalKit, EMMA-mini, MMK12, and the rule-based post-processing helpers.

## 1) vLLM server does not answer

Symptoms:

- client requests time out
- the evaluation client cannot reach the served model
- the server is listening on the wrong port or the wrong model name

Checks:

- Confirm that the launch command used the expected port and served model name.
- Confirm that the client base URL points at the same endpoint.
- Check that the GPU count matches the tensor parallel size.

Recovery:

- Keep the model name `r1v3-alpha` aligned across server and client.
- Lower tensor parallelism if the GPU layout changed.
- Rebuild the launch command with the bundled helper before starting the server.

## 2) Benchmark scripts fail before scoring

Symptoms:

- dataset lookup fails
- the client cannot find `LMDEPLOY_API_KEY`
- `LMDEPLOY_API_BASE` points at the wrong endpoint
- `USE_COT` is set inconsistently with the chosen benchmark path

Checks:

- Review the printed command bundle before launching anything.
- Confirm that benchmark caches and downloads exist.
- For PhyX, ensure the TSV lands in the expected `LMUData` location.

Recovery:

- Re-export the environment variables.
- Re-run the command bundle with the correct dataset names.
- Use `run_phyx.py` only for the dataset path that expects it.

## 3) Rule-based post-processing looks wrong

Symptoms:

- MMMU or LogicVista scores do not match expectations
- the last boxed answer is not being selected
- val-only rows are missing or filtered incorrectly

Checks:

- Use `score_boxed_answers.py` against a tiny fixture first.
- Confirm whether the benchmark expects a val-only filter.
- Check that the annotated output still contains the source prediction and answer fields.

Recovery:

- Normalize the last boxed answer.
- Keep MMMU and LogicVista separated in the post-processing step.
- If the output is xlsx, inspect the sheet names and row counts with the bundled output checker.

## 4) EMMA-mini generation problems

Symptoms:

- prompt assembly fails
- responses are blank or contain `Response Error`
- local model adapters do not match the checkpoint name

Checks:

- Confirm the YAML prompt template path exists.
- Confirm the selected subjects and strategy are valid.
- Check whether the workflow is using a remote API or a local model path.

Recovery:

- Switch the `model_path` branch only when the checkpoint name clearly matches one of the supported adapters.
- Keep incremental output writes enabled for long runs.
- Validate the result JSON with the bundled output checker before scoring.

## 5) MMK12 generation or judge scoring problems

Symptoms:

- the local OpenAI-compatible endpoint is unreachable
- the judge client returns something other than `Yes` or `No`
- the output directory is empty or partially written

Checks:

- Confirm the served model name is still `r1v3-alpha`.
- Confirm that the base URL matches the local endpoint.
- Check that the MMK12 dataset can be fetched and cached.

Recovery:

- Reduce concurrency if the local endpoint becomes unstable.
- Keep judge credentials out of the runtime files.
- If a response already exists, inspect whether the boxed-answer or `<answer>` extraction logic is the cause.

## 6) When to switch sub-skills

- If the task is only to build a request payload or parse tagged R1V4 responses, route to `r1v4-api-testing`.
- If the task is only a local inference command or image-grid estimate, route to `local-inference`.
- If the task is only a model-serving API batch issue, stay here only when the flow is specifically VLMEvalKit, EMMA, or MMK12.
