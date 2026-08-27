# Troubleshooting Architecture and Training Plans

Use this reference to diagnose command-plan failures without running heavyweight native jobs.

## Fast Triage Table

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `checkpoint` or `model` file not found | Placeholder path, wrong checkpoint filename, rank-specific path mismatch | Ask for explicit checkpoint/model directory; validate with `check_training_plan.py`. |
| YOCO needle command OOMs | `--tokens-per-sample`/`--interval` too high, batch too large, missing long-context kernels | Reduce context first, keep batch `1`, verify bf16/kernel support. |
| Distributed launch hangs | `MASTER_ADDR`/`PORT`/`NNODES` mismatch or a missing worker | Reconcile all ranks and confirm port reachability. |
| `No module named fairseq` or plugin import failure | Old vendored fairseq path not active, wrong working directory, missing `--user-dir` | Treat as environment/setup issue; do not edit generated skill content to depend on source paths. |
| Flash/Apex import failure | Optional CUDA extension not installed or incompatible | Verify PyTorch/CUDA/SM versions; fall back to non-kernel inspection only if possible. |
| DeepSpeed ZeRO checkpoint confusion | Sharded checkpoints or resume scanning output dir | Use documented DeepSpeed load/save paths; keep dry-run outputs isolated. |
| PFPO OpenAI/service caller fails | Missing API key, endpoint, Hydra model config, or network service | Do not run credentialed callers; use offline validation alternatives. |
| PFPO/PFPO math JSONL mismatch | Expected keys differ across scripts | Inspect a few records and normalize keys before evaluation or pair construction. |
| ReSA result collector cannot find file | Output filename differs from `save_feature` pattern | List output folder and pass the actual JSONL filename to collection scripts. |
| RetNet config rejects `--subln`/`--deepnorm` | RetNet README states DeepNet initialization is integrated | Remove those flags unless the exact RetNet config documents them. |

## YOCO Needle Evaluation Failures

A YOCO needle plan needs a checkpoint, YOCO model directory, process count, and context settings. Missing any of these should block launch.

Checklist:

- `--load-ckpt` points to a checkpoint file, not just a directory.
- `--yoco-model` points to the model directory used by the checkpoint.
- `--tokens-per-sample` and `--interval` are positive and normally equal for the benchmark-style needle run.
- `--needle-num` is only used with `multi_needle`.
- `--nproc_per_node` does not exceed visible GPUs.
- `--batch-size` remains `1` for 1M-token context unless there is explicit memory evidence.

If the user asks for a sanity check, run a command like:

```bash
python scripts/check_training_plan.py yoco-needle --checkpoint CHECKPOINT_PTH --model-dir YOCO_MODEL_DIR --tokens-per-sample 1048576 --interval 1048576 --nproc-per-node 1 --needle-num 4
```

Then explain warnings rather than launching native `validate.py`.

## PFPO Credentialed Caller Blockers

PFPO has two top-level credential/service callers:

- `openai_api_caller_v1.py`: constructs a Hydra model and logs OpenAI API inference.
- `service_api_caller_v1.py`: loads a dataset and post-processor for service-style outputs.

Do not run these unless the user confirms credentials, endpoint/service availability, cost acceptance, and the exact Hydra config. Without that, offer offline alternatives:

- Validate input file existence and JSON/JSONL parseability.
- Verify MBPP test case structure using a sandboxed local process.
- Construct preference pairs from existing local predictions.
- Prepare a checklist of missing credentials and config names.

## PFPO Offline Format Checks

Common expected records vary by script. Use these source-derived expectations:

- Math SFT-style data: list items may include `question`, `box_solution`, and `id`.
- Inference data: list items often include `question`, `id`, and `label`.
- MBPP verification: program predictions are JSON lists with `task_id`, `completion`, and `passed`; test-case predictions may be JSON mapping task id to cases or JSONL with `task_id` and `completion` containing `[BEGIN] ... [END]` assert lines.
- Preference construction: many scripts accept globbed input paths and write one output JSON file.

JSONL mismatch symptoms include `KeyError`, empty result sets, all test cases missing, or all programs marked bad. Inspect representative records and normalize keys before rerunning.

## GAD/IAD Decoding Failures

GAD requires both a NAT drafter and an AR verifier checkpoint. Failure patterns:

- Missing dictionary files in `DATA_DIR`: fairseq data was not binarized or wrong data root supplied.
- `--AR-path` missing: GAD verification cannot run; use baseline/fairseq strategy only if the user intended that.
- `--user-dir block_plugins` import failure: plugin path not discoverable from the working directory.
- Bad `--block-size`, `--beta`, or `--tau`: aggressive settings can degrade quality or make verification ineffective.
- Output path unwritable: pre-create parent directory for result text.

IAD has its own vendored fairseq. Do not mix IAD and GAD checkpoint/runtime assumptions.

## ReSA Math Evaluation Failures

ReSA sparse decoding can fail because of data, checkpoint, or kernel issues:

- Missing checkpoint/tokenizer artifacts: confirm `--checkpoint_dir` contains the expected model files.
- CUDA/kernel import failure: flash attention or sparse kernel is incompatible with the current PyTorch/CUDA/GPU.
- OOM during prefill: reduce `--batch_size`, `--limit`, or max sequence length; keep `--nproc_per_node=1` for smoke tests.
- Bad `save_feature`: result file names may not match the collection command.
- JSONL aggregation errors: pass the actual result filename and confirm each line is valid JSON.

## Benchmark-Scale Run Safety

Before any benchmark-scale run, ask the user to confirm:

- Expected wall time and cost.
- GPU type/count and memory.
- Whether downloads or credentialed services are allowed.
- Output location and retention policy.
- Whether a smaller smoke test should run first.

A safe smaller smoke test usually uses one GPU, tiny `--limit`, short context length, and local placeholder data. Do not imply that a smoke test validates full benchmark quality.
