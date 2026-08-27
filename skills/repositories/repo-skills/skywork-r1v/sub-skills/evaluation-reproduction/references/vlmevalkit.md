# VLMEvalKit Skywork flow

This reference distills the Skywork-specific VLMEvalKit evaluation recipe into self-contained command shapes and prerequisites. Use the bundled command builder instead of copying shell snippets by hand.

## Environment setup boundary

A full native benchmark run needs a heavy evaluation environment, including:

- the VLMEvalKit requirements used by the Skywork evaluation tree
- `vllm==0.8.3`
- `torchao`
- system `libgl1`
- `modelscope`
- CUDA-compatible PyTorch and a local model checkpoint

Treat that setup as an explicit benchmark environment, not as a safe helper step. The bundled scripts in this sub-skill only build commands and inspect outputs; they do not install the heavy stack.

## Launch the served model

The stock Skywork recipe serves the model through a vLLM OpenAI-compatible API server. The important values are:

| Setting | Stock value or role |
| --- | --- |
| served model name | `r1v3-alpha` |
| port | `8000` |
| image limit | `image=60` |
| max model length | `32768` |
| tensor parallel size | `8` |
| GPU memory utilization | `0.8` |
| trust remote code | enabled |

Generate the launch command with:

```bash
python scripts/build_eval_commands.py launch-server \
  --model-path /path/to/r1v3-model \
  --tensor-parallel-size 8
```

The command builder prints the vLLM server command without starting it.

## `run.py` / `run_phyx.py` command surface

The Skywork wrapper around VLMEvalKit uses these CLI arguments:

- `--data` for one or more benchmark names
- `--model` for one or more model names
- `--config` as an alternative to `--data`/`--model`
- `--work-dir` for the output root
- `--mode all|infer` to run inference plus evaluation or inference only
- `--api-nproc` for parallel API calls
- `--retry` for API retries
- `--judge` for an explicit judge model
- `--verbose` for more logging
- `--ignore` to skip failed indices
- `--reuse` to reuse the latest prediction and temporary files
- `--reuse-aux` to reuse auxiliary evaluation files too
- `--use-vllm` for model classes that support the flag

Behavior constraints:

- `--config` is mutually exclusive with `--data` and `--model`.
- `--mode infer` skips the evaluation phase.
- `--reuse` changes whether old predictions and temporary files are copied forward.
- `--reuse-aux` broadens reuse to auxiliary evaluation artifacts.
- Keep `LMDEPLOY_API_BASE` aligned with the served model endpoint.

## Standard benchmark command shape

Generate a benchmark command bundle with:

```bash
python scripts/build_eval_commands.py vlmeval \
  --data LogicVista \
  --api-nproc 16
```

The command builder prints a placeholder-based bundle that expects:

- `SKYWORK_EVAL_ROOT` to point to a prepared Skywork-compatible evaluation tree when you intentionally run the native benchmark scripts.
- `BUNDLED_EVAL_SKILL_DIR` to point to this sub-skill directory when using the bundled scorer.
- `LMDEPLOY_API_KEY` and `LMDEPLOY_API_BASE` to be configured at runtime.

The standard Skywork flow uses `USE_COT=1` for the regular VLMEvalKit path. For PhyX, the command builder switches to `run_phyx.py` and `USE_COT=0` when `--phyx` is set or the dataset is `PHYX`.

## Rule-based post-processing

Some benchmarks need extra scoring after VLMEvalKit writes its result file:

- `MMMU` extracts and normalizes the last `\boxed{...}` answer and only keeps rows whose id starts with `val`.
- `LogicVista` uses the same boxed-answer normalization without the MMMU val filter.

Use the bundled safe scorer for this step:

```bash
python scripts/score_boxed_answers.py --input result.jsonl --val-only
python scripts/score_boxed_answers.py --input logicvista_result.xlsx
```

The scorer accepts JSON, JSONL, and XLSX inputs when the supporting packages are installed.

## Output inspection

Use the output checker before trusting a full benchmark result:

```bash
python scripts/check_eval_outputs.py --input result.jsonl summary.json result.xlsx --json
```

The checker reports file existence, JSON/JSONL record counts, common keys, and XLSX sheet dimensions.

## Failure handling

Common Skywork/VLMEvalKit failures usually come from one of these causes:

- the server is not reachable on port 8000
- the GPU count does not match tensor parallel size
- the model path placeholder was never replaced
- the judge key or base URL is missing
- `api-nproc` is too high for the local endpoint
- the PhyX TSV is not placed under the prepared evaluation tree's `eval/vlmevalkit/eval_shell/LMUData` directory

Use `references/troubleshooting.md` for the exact checks and fixes.
