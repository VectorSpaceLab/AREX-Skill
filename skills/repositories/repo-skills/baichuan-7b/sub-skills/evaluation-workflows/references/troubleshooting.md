# Evaluation Troubleshooting

Use this when C-Eval or MMLU preflight or execution fails. For model-loading internals, cross-check [architecture-and-loading](../../architecture-and-loading/SKILL.md). For shared package/API issues, use the root [API reference](../../../references/api-reference.md) and [troubleshooting](../../../references/troubleshooting.md).

## Quick triage

1. Run the bundled helper in the matching mode before retrying the benchmark:

   ```bash
   python sub-skills/evaluation-workflows/scripts/check_evaluation_inputs.py ceval --repo-root /path/to/Baichuan-7B --model /path/to/model --check-imports --check-cuda
   python sub-skills/evaluation-workflows/scripts/check_evaluation_inputs.py mmlu --repo-root /path/to/Baichuan-7B --benchmark-root /path/to/hendrycks-test --model /path/to/model --check-imports --check-cuda
   ```

2. Confirm the model path resolves locally or that the runtime can access the model id/cache.
3. Confirm CUDA is available; both scripts move input tensors to CUDA.
4. Confirm benchmark data source:
   - C-Eval: `datasets.load_dataset("ceval/ceval-exam", task_name)` can resolve every task config and the requested split.
   - MMLU: benchmark root contains `categories.py`, `data/dev`, and `data/test` with paired CSVs.
5. If the script starts but artifacts are incomplete, inspect stdout/stderr around the first failed task/subject; aggregate summaries may not be written when a run aborts.

## C-Eval failures

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'datasets'` | Hugging Face `datasets` is not installed in the active environment. | Install/activate an environment with `datasets`, `torch`, `transformers`, `numpy`, and `tqdm`. The user's benchmark runtime must match the model and CUDA requirements. |
| `ConnectionError`, dataset download failure, or cache miss for `ceval/ceval-exam` | `evaluate_zh.py` uses `datasets.load_dataset("ceval/ceval-exam", task_name)` and does not accept a local data directory option. | Run online once to populate cache, configure the Hugging Face datasets cache, or adapt the script explicitly for a local dataset. In offline mode, verify every task config and split is cached. |
| `KeyError: '<split>'` or split not found | `--split` is not present for a C-Eval task. | Use the script default `--split val` unless you know the dataset cache has a labeled `dev`/`test` split. Remember `dev` is also used for few-shot examples. |
| Accuracy computation fails because `answer` is missing | The selected split does not include labels. | Use a labeled split (`val` is the safe default for the native script). The script compares `answer == data["answer"]` and cannot score unlabeled test rows. |
| Output directory error on startup | `--output_dir` parent does not exist or a conflicting file exists. `CEval.__init__` only calls `os.mkdir(output_dir)`. | Use a simple new directory such as `ceval_output` under an existing parent, or create the parent first. |
| Very slow first task | Dataset config download/cache build or model loading is happening at runtime. | Pre-cache dataset/model, verify the model path, and capture logs. The helper intentionally does not fetch data or load weights. |

## MMLU failures

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'categories'` | The MMLU evaluation entrypoint is not adjacent to Hendrycks/test `categories.py`, or Python is running from another directory. | Validate the benchmark root with the bundled helper. A real MMLU run needs an evaluation entrypoint beside `categories.py`; do not rely on a script path that cannot import the benchmark categories module. |
| `FileNotFoundError: data/test` or no subjects discovered | MMLU `data.tar` was not extracted, or `--data_dir` points to the wrong location. | Ensure `data/test/*_test.csv` exists under the benchmark root or pass the correct `-d/--data_dir`. |
| `FileNotFoundError: data/dev/<subject>_dev.csv` | A test subject has no paired dev CSV. | Re-extract the official MMLU data or remove the incomplete subject only if intentionally running a narrowed custom benchmark. |
| `KeyError` from `subcategories[subject]` | `categories.py` does not contain a mapping for a subject inferred from `*_test.csv`. | Use the matching Hendrycks/test `categories.py` and dataset release, or update the category map for custom subjects. |
| CSV parsing looks shifted or answer labels are wrong | CSV rows do not follow question + four choices + answer format. | Validate sample rows with the helper. MMLU rows should have at least six columns, and the answer label must be `A`, `B`, `C`, or `D`. |
| Prompt processing hangs or runs extremely slowly before scoring one example | The truncation loop cannot get under 2048 tokens, especially for a very long test row. The script decrements `k` repeatedly and has awkward behavior at `k == -1`. | Run the helper and inspect prompt-length warnings. Reduce `--ntrain`, remove or shorten malformed long rows, or patch the script with a lower-bound guard (`k = max(k - 1, 0)` and fail if zero-shot still exceeds 2048 tokens). |
| Result directory is nested unexpectedly, for example `results/results_/path/to/model/...` | `evaluate_mmlu.py` uses the raw `--model` argument inside `results_<model>`. Slashes create nested path components. | Prefer a local model path/name that produces acceptable output paths, or move/rename result directories after the run. Capture stdout for aggregate metrics. |
| `--ngpu` has no effect | The argument is parsed but never used. | Rely on `device_map="auto"`, CUDA visibility (`CUDA_VISIBLE_DEVICES`), and Transformers/Accelerate behavior instead. |

## CUDA/backend failures

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| `AssertionError: Torch not compiled with CUDA enabled` or `RuntimeError: Found no NVIDIA driver` | Runtime PyTorch is CPU-only or the host has no visible CUDA driver/GPU. | Use a CUDA-enabled PyTorch environment and verify `python -c 'import torch; print(torch.cuda.is_available())'`. The helper's `--check-cuda` performs a tiny allocation probe. |
| Device mismatch around logits/input tensors | The scripts call `.cuda()` on inputs while loading the model with `device_map="auto"`; unusual offload/device maps can create mismatches. | Prefer a single visible CUDA device for the native scripts, or patch input placement to the model's first execution device if using advanced offload. |
| CUDA out of memory during model load or first task | 7B weights plus activations/logits do not fit the visible GPU setup. | Free memory, reduce other processes, use a larger GPU, or adapt evaluation to a supported quantized/offloaded path. Static preflight cannot prove full memory sufficiency. |
| `torch.cuda.is_bf16_supported()` is false for C-Eval | C-Eval falls back to `torch.float32`, increasing memory. | Expect higher memory pressure. Use hardware with bf16 support or adapt dtype carefully if validated. |

## Model/checkpoint failures

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| `OSError` from `from_pretrained` saying files are missing | Model id/path does not contain weights, config, tokenizer, or remote-code metadata. | Verify the local checkpoint directory has `config.json`, tokenizer files, and weight shards (`*.bin` or `*.safetensors`), or use a reachable model id/cache. |
| Remote-code/trust error | Baichuan uses a custom model/tokenizer implementation and the native scripts set `trust_remote_code=True`. | Ensure policy permits remote code from the trusted checkpoint source. For local mirrors, keep the required modeling/tokenization files or `auto_map` metadata. |
| Tokenizer loading fails | Missing `tokenizer.model`, tokenizer config, SentencePiece dependency, or mismatched files. | Use the official Baichuan tokenizer assets and an environment with tokenizer dependencies. Cross-check loading guidance in [architecture-and-loading](../../architecture-and-loading/SKILL.md). |

## Import/dependency failures

If imports fail, first print the active Python path/version and package versions, then activate or recreate the intended benchmark environment. C-Eval and MMLU share model-loading dependencies, but each has its own data-package and layout requirements.

Benchmark-specific package map:

- C-Eval: `datasets`, `tqdm`, `numpy`, `torch`, `transformers`.
- MMLU: `pandas`, `numpy`, `torch`, `transformers`, plus a local `categories.py` in the benchmark root.

## Output and recovery notes

- C-Eval writes per-task JSON files and `acc.json`; if interrupted, inspect which task JSON files exist before deciding whether to rerun from scratch.
- MMLU writes per-subject CSVs; aggregate metrics are stdout-only, so preserve logs for reports.
- Neither script has native resume logic. Safe reruns should use a fresh output directory or intentionally overwrite known partial artifacts.
- The sub-skill helper only validates and renders; it does not mutate benchmark data or launch model inference.
