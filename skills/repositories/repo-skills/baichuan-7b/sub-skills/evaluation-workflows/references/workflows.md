# C-Eval and MMLU Evaluation Workflows

This reference distills the Baichuan-7B README/README_EN benchmark sections plus the behavior of `evaluation/evaluate_zh.py` and `evaluation/evaluate_mmlu.py`. It is self-contained for operating decisions: use source filenames as provenance labels, not as required evidence reads.

## Execution status and safe boundaries

- Public checkpoint identity used in examples: `baichuan-inc/Baichuan-7B` or a local compatible checkpoint directory.
- Required runtime dependencies for real benchmark runs include `datasets`, `pandas`, `torch`, `transformers`, and a CUDA-capable model-loading environment.
- Native candidates `ceval-eval` and `mmlu-eval` are full benchmark workflows; this skill's bundled helper performs static/layout validation and command planning, not end-to-end benchmark inference.
- Bundled helper: [check_evaluation_inputs.py](../scripts/check_evaluation_inputs.py) validates layout and renders commands without loading weights, fetching datasets, or executing benchmark inference.

## Shared model/runtime prerequisites

Both native evaluation scripts load Baichuan through Hugging Face Transformers with `trust_remote_code=True` and then move tokenized inputs to CUDA.

Minimum expectations before a real run:

1. A Baichuan-7B-compatible model identifier or local checkpoint directory.
2. Checkpoint weights and tokenizer files available locally or through the configured Hugging Face/ModelScope cache/network path.
3. `torch`, `transformers`, and benchmark-specific packages installed.
4. CUDA available. The scripts call `.cuda()` on input tensors, and MMLU forces `torch_dtype=torch.bfloat16` while using `device_map="auto"`.
5. Enough GPU memory for 7B causal-LM scoring across all benchmark examples. Static preflight cannot prove full memory sufficiency.
6. `trust_remote_code=True` accepted for the Baichuan custom model/tokenizer implementation. For model-loading details, use sibling [architecture-and-loading](../../architecture-and-loading/SKILL.md).

Typical local-checkpoint sanity before benchmark launch:

```bash
python sub-skills/evaluation-workflows/scripts/check_evaluation_inputs.py ceval \
  --repo-root /path/to/Baichuan-7B \
  --model /path/to/Baichuan-7B-weights \
  --check-imports \
  --check-cuda
```

The helper can validate a local model directory for common artifacts such as `config.json`, tokenizer files, and weight shards. If the model argument is a remote id, it reports that the cache/network path must be resolved at runtime.

## C-Eval workflow

### What the native script does

`evaluation/evaluate_zh.py` defines `CEval.DATA_PATH = "ceval/ceval-exam"` and evaluates every task in its built-in 52-task `TASK2DESC` map.

For each task:

1. Load the dataset with `datasets.load_dataset("ceval/ceval-exam", task_name)`.
2. Build a Chinese multiple-choice prompt:
   - task-specific exam description;
   - up to `--shot` examples sampled from the dataset `dev` split;
   - one unlabeled target item from the requested `--split`.
3. Tokenize with `AutoTokenizer.from_pretrained(..., trust_remote_code=True, use_fast=True, add_bos_token=False, add_eos_token=False, padding_side="left")`.
4. Move `input_ids` to CUDA with `.cuda()`.
5. Score the last-token logits for labels `A`, `B`, `C`, and `D`.
6. Select the label with highest softmax probability and compare with `data["answer"]`.
7. Save one JSON result file per task and `acc.json` for per-task accuracy.

Model loading is:

```python
AutoModelForCausalLM.from_pretrained(
    model_name_or_path,
    trust_remote_code=True,
    device_map="auto",
    torch_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float32,
)
```

### Native options

| Option | Default | Meaning | Operational notes |
| --- | --- | --- | --- |
| `--model_name_or_path` | required | Local checkpoint path or model id. | Must resolve weights/tokenizer/custom code at runtime. |
| `--shot` | `5` | Few-shot examples from `dev`. | Must be non-negative. If greater than the dev split length, the script uses all available dev rows. |
| `--split` | `val` | Dataset split to score. | The script does not validate the name before indexing `dataset[split]`; use `val` for scored validation unless the target cache/source really has another labeled split. |
| `--output_dir` | `ceval_output` | Directory for JSON artifacts. | Created with `os.mkdir`; parent directories must already exist. |

### Command construction

Use the bundled helper to validate inputs and render the C-Eval command shape before any real benchmark run:

```bash
python sub-skills/evaluation-workflows/scripts/check_evaluation_inputs.py ceval \
  --repo-root /path/to/Baichuan-7B \
  --model /path/to/Baichuan-7B-weights \
  --shot 5 \
  --split val \
  --output-dir ceval_output
```

### C-Eval data prerequisites

The actual script does not accept a local C-Eval path flag. It relies on Hugging Face `datasets` resolving `ceval/ceval-exam` for every task name. Therefore preflight should make the data-routing assumption explicit:

- online run: the host can reach and download the dataset through `datasets`;
- offline run: the dataset and all task configs are already present in the Hugging Face datasets cache;
- split availability: the selected `--split` plus `dev` must exist for every task;
- label availability: the selected split must contain `question`, `A`, `B`, `C`, `D`, and `answer` fields because the script computes accuracy locally.

If a user asks for a local C-Eval directory, explain that the native script would need adaptation because `DATA_PATH` is hard-coded to `ceval/ceval-exam` and there is no `--data_dir` option.

### C-Eval output artifacts

Default output directory: `ceval_output`.

Expected files after a complete run:

- one task JSON per `TASK2DESC` key, for example `high_school_physics.json`;
- `acc.json`, a JSON object mapping each task name to its accuracy;
- stdout includes `average acc: <float>` after all tasks finish.

Each per-task JSON is a list of records like:

```json
{
  "prompt": "...",
  "correct": true,
  "answer": "A"
}
```

Important artifact limits:

- Per-example probabilities are not saved by `evaluate_zh.py`.
- The global average is printed to stdout, not stored separately unless the user captures logs.
- Partial runs may leave some task JSON files without a complete `acc.json`.

## MMLU workflow

### What the native script does

`evaluation/evaluate_mmlu.py` is derived from the Hendrycks/test evaluation layout. It imports `subcategories` and `categories` from a sibling `categories.py`, so the script must run from a benchmark checkout where `categories.py` is importable.

For each subject inferred from `data/test/*_test.csv`:

1. Read `data/dev/<subject>_dev.csv` and keep the first `--ntrain` rows.
2. Read `data/test/<subject>_test.csv`.
3. Build an English multiple-choice prompt with `--ntrain` dev examples and one test example.
4. Tokenize with `AutoTokenizer.from_pretrained(model, use_fast=False, add_bos_token=False, model_max_length=4096, padding_side="right", trust_remote_code=True)`.
5. If `input_ids.shape[-1] > 2048`, decrement the few-shot count and rebuild until it fits.
6. Move inputs to CUDA, score answer-token logits for `A`/`B`/`C`/`D`, and compute correctness.
7. Save per-subject CSVs with correctness/probability columns.
8. Print subject, subcategory, category, and weighted-average accuracies to stdout.

Model loading is:

```python
AutoModelForCausalLM.from_pretrained(
    model,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True,
)
```

The `--ngpu/-g` argument is parsed but unused by this script.

### Native options

| Option | Default | Meaning | Operational notes |
| --- | --- | --- | --- |
| `--model`, `-m` | `google/flan-t5-small` | Model id or local checkpoint path. | Always override this with the Baichuan checkpoint. Raw slashes are reused in result directory and column names. |
| `--ntrain`, `-k` | `5` | Number of dev examples in prompt. | Prompt guard may reduce this per example to fit 2048 tokens. |
| `--data_dir`, `-d` | `data` | MMLU data directory. | Must contain `dev/` and `test/` with paired subject CSVs. |
| `--save_dir`, `-s` | `results` | Root output directory. | Script creates `save_dir` and `save_dir/results_<model>`. |
| `--ngpu`, `-g` | `8` | Parsed but unused. | Do not rely on it for device placement. |

### Required Hendrycks/test layout

The README reproduction flow is:

```bash
git clone https://github.com/hendrycks/test
cd test
wget https://people.eecs.berkeley.edu/~hendrycks/data.tar
tar xf data.tar
mkdir results
cp ../evaluate_mmlu.py .
python evaluate_mmlu.py -m /path/to/Baichuan-7B
```

Operationally, the benchmark root must look like:

```text
hendrycks-test/
  categories.py
  evaluate_mmlu.py          # copied from the Baichuan repo or otherwise adjacent to categories.py
  data/
    dev/
      abstract_algebra_dev.csv
      ...
    test/
      abstract_algebra_test.csv
      ...
  results/                  # optional; script creates it if missing
```

Each subject in `data/test/*_test.csv` must have:

- matching `data/dev/<subject>_dev.csv`;
- a key in `subcategories` from `categories.py`;
- CSV rows with question text, four choices, and an answer label in `A`/`B`/`C`/`D`.

### Command construction

Use the bundled helper to validate the Hendrycks/test layout and render the MMLU command shape before any real benchmark run. A real run requires an evaluation entrypoint adjacent to `categories.py` inside the benchmark workspace; the helper reports that requirement instead of executing the benchmark:

```bash
python sub-skills/evaluation-workflows/scripts/check_evaluation_inputs.py mmlu \
  --repo-root /path/to/Baichuan-7B \
  --benchmark-root /path/to/hendrycks-test \
  --model /path/to/Baichuan-7B-weights \
  --data-dir data \
  --save-dir results \
  --ntrain 5
```

### MMLU prompt truncation behavior

The native script truncates by reducing the few-shot count while the tokenized prompt exceeds 2048 tokens:

```python
while input_ids.shape[-1] > 2048:
    k -= 1
    train_prompt = gen_prompt(dev_df, subject, k)
    prompt = train_prompt + prompt_end
    input_ids = tokenizer(prompt, return_tensors="pt").input_ids.cuda()
```

Implications:

- The requested `--ntrain` is a maximum, not a guarantee for every example.
- If a single test example is longer than 2048 tokens even with zero dev examples, the loop can keep decrementing and fail to make progress.
- When `k` reaches `-1`, `gen_prompt` treats that as "use all dev rows", so one iteration can unexpectedly lengthen the prompt before later negative values produce no examples.
- The helper performs a conservative character-length guard over sampled prompts. Exact token-length validation requires the real tokenizer and is intentionally not done by default because it can trigger model/tokenizer downloads or remote-code loading.

### MMLU output artifacts

Default output root: `results`.

Expected files after a complete run:

```text
results/
  results_<model-argument>/
    abstract_algebra.csv
    anatomy.csv
    ...
```

Each per-subject CSV contains the original test rows plus:

- `<model>_correct`: boolean correctness per example;
- `<model>_choiceA_probs`, `<model>_choiceB_probs`, `<model>_choiceC_probs`, `<model>_choiceD_probs`: answer-choice probabilities.

Stdout includes:

- `Average accuracy <acc> - <subject>` for each subject;
- subcategory and category average lines;
- final `Average accuracy: <weighted_acc>`.

Important artifact limits:

- Aggregate metrics are printed, not written to a JSON/CSV summary by the native script.
- If the `--model` argument contains slashes, the result directory becomes nested under `results_<model>` path components, and generated column names contain the raw model string. Prefer a local path or capture stdout carefully if result names matter.
- Partial runs may contain some subject CSVs without all categories printed.

## Preflight helper responsibilities

[check_evaluation_inputs.py](../scripts/check_evaluation_inputs.py) is safe by design and owned by this sub-skill.

It can:

- validate native evaluation script presence under a supplied Baichuan repo root;
- check local model directory artifacts without loading weights;
- optionally import Python dependencies (`--check-imports`);
- optionally check CUDA and perform a tiny allocation (`--check-cuda`);
- validate C-Eval option ranges and dataset-routing assumptions;
- validate MMLU `categories.py`, `data/dev`, `data/test`, paired subjects, sample CSV rows, and conservative prompt-length risks;
- render the exact native commands to run manually.

It does not:

- fetch `ceval/ceval-exam`;
- download MMLU data;
- load Baichuan model weights;
- import or execute arbitrary `categories.py` code;
- run C-Eval/MMLU inference.

## Cross-links

- Parent skill: [Baichuan-7B root](../../../SKILL.md)
- Root API reference: [api-reference](../../../references/api-reference.md)
- Shared troubleshooting: [root troubleshooting](../../../references/troubleshooting.md)
- Model-loading prerequisites: [architecture-and-loading](../../architecture-and-loading/SKILL.md)
- Training-only setup: [pretraining-and-deepspeed](../../pretraining-and-deepspeed/SKILL.md)
- Local troubleshooting: [troubleshooting](troubleshooting.md)
- Local helper: [check_evaluation_inputs.py](../scripts/check_evaluation_inputs.py)
