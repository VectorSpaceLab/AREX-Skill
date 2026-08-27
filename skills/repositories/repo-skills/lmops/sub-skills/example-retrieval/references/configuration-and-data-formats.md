# Configuration and data formats

Use this reference when a request is really about task names, metric names, prompt-pool shapes, scored-data files, or command-argument validation.

## Planning workflow

1. Write a tiny JSON plan with the fields you know.
2. Run `../scripts/validate_task_metric_plan.py` to catch mismatches before editing source task maps or command flags.
3. Run `../scripts/build_retrieval_commands.py` to print the safe command templates for the chosen workflow family.

The validator and planner do not import repository code.

## UPRISE and SE2 task/metric map

The most common validation error is a task/metric mismatch. The following distilled map is enough for planning.

### Classification and selection tasks

| Task | Expected metric | Typical class count | Notes |
| --- | --- | --- | --- |
| `mnli` | `simple_accuracy` | 3 | Training split is MNLI; matched/mismatched variants are evaluation aliases. |
| `mnli_m` / `mnli_mm` | `simple_accuracy` | 3 | Inherit from `mnli`; do not train them separately. |
| `qnli` | `simple_accuracy` | 2 | |
| `rte` | `simple_accuracy` | 3 in the distilled UPRISE map | UPRISE and SE2 both use the public task implementation as the source of truth. |
| `snli` | `simple_accuracy` | 3 | |
| `boolq` | `simple_accuracy` | 2 | UPRISE only. |
| `multirc` | `f1` | 2 | UPRISE only. |
| `openbookqa` | `simple_accuracy` | 4 | `finder_L` is larger than the default because the candidate pool is richer. |
| `copa` | `simple_accuracy` | 2 | Often used as the smallest SE2 sanity task. |
| `hellaswag` | `simple_accuracy` | 4 | |
| `piqa` | `simple_accuracy` | 2 | UPRISE only. |
| `sentiment140` | `simple_accuracy` | 2 | |
| `sst2` | `simple_accuracy` | 2 | |
| `yelp` | `simple_accuracy` | 2 | UPRISE only. |
| `arc_c` | `simple_accuracy` | 4 | |
| `arc_e` | `simple_accuracy` | 4 | Inherits the ARC-Challenge-style task shape. |
| `mrpc` | `acc_and_f1` | 2 | |
| `qqp` | `acc_and_f1` | 2 | |
| `paws` | `simple_accuracy` | 2 | |
| `wsc` | `simple_accuracy` | 2 | UPRISE only. |
| `wsc273` | `simple_accuracy` | 2 | UPRISE test-only alias. |
| `winogrande` | `simple_accuracy` | 2 | UPRISE only. |
| `ag_news` | `simple_accuracy` | 4 | SE2 task cluster uses this name. |
| `sst5` | `simple_accuracy` | 5 | SE2 only. |
| `pubmed_qa` | `pubmed_qa_acc` | 1 | CoT prompting example in UPRISE/SE2 maps. |

### Generation / text-completion tasks

| Task | Expected metric | Typical class count | Notes |
| --- | --- | --- | --- |
| `squad_v1` | `squad` | 1 | UPRISE only. |
| `natural_questions` | `trivia_qa` | 1 | UPRISE only. |
| `common_gen` | `rouge` | 1 | |
| `dart` | `rouge` | 1 | UPRISE only. |
| `e2e_nlg` | `rouge` | 1 | |
| `aeslc` | `rouge` | 1 | |
| `gigaword` | `rouge` | 1 | |
| `roc_story` | `rouge` | 1 | SE2 only. |
| `roc_ending` | `rouge` | 1 | SE2 only. |

### Cluster strings

- **UPRISE** train clusters are grouped by family names such as `close_qa`, `common_reason`, `coreference`, `nli`, `paraphrase`, `reading`, `sentiment`, `struct2text`, and `summarize`.
- **UPRISE** test clusters use the same family names and add quick-example and CoT aliases such as `train_example_1`, `test_example_1`, and `cot_test_example`.
- **SE2** uses task names as cluster names. The main exception is `mnli`, which expands to `mnli_m` and `mnli_mm` internally.

When validating a cluster string, remember that `+` means concatenation of cluster names, not arithmetic.

## UPRISE prompt-pool and scored-data shapes

UPRISE command planning is easiest when you remember the file roles:

- **Prompt pool**: JSON file or directory tree containing task-specific prompt examples.
- **Random sample file**: prompt IDs selected for scoring.
- **Scored train/valid files**: JSON files with per-candidate scores and split data.
- **Retrieved prompt file**: JSON file with the selected prompt IDs for the test task.
- **Prediction/result files**: model outputs and task-level metric summaries.

Common fields that appear in the distilled UPRISE readers and scripts:

- `id`: prompt or example identifier.
- `task_name`: task name carried through the pipeline.
- `meta_data`: raw example payload used to reconstruct questions and answers.
- `ctxs`: list of candidate prompt references, each with an `id` field.
- `query`, `answers`, `options`: task reader columns.
- `query_id`: unique identifier added to formatted task rows.

The prompt-pool files that feed retriever training and inference are deliberately task-local. Do not mix unrelated prompt-pool JSON files unless the task plan intentionally uses a multi-task cluster.

## SE2 scored-data shapes

SE2 adds multi-step fields to the example and scored-data JSON files:

- `step_1_have_choosen`, `step_1_ctxs`
- `step_2_have_choosen`, `step_2_ctxs`
- `step_3_have_choosen`, `step_3_ctxs`
- `choosen`
- `ctxs` for the active candidate set at the stage being scored

The merge step consumes the step-wise JSON files and writes final merged train/valid files. If a stage file is missing, check whether the previous stage was skipped or whether the output path was changed in the generated command plan.

## LLM Retriever file formats

### Core JSONL inputs

The formatter and training code use these field shapes:

- `passages.jsonl.gz`: `id`, `contents`, `task_name`
- `train.jsonl.gz` / `test.jsonl.gz`: `query_id`, `query`, `answers`, `options`, `task_name`

### Derived retrieval/scoring outputs

- Search output adds `doc_ids` and `doc_scores`.
- Readable output converts the top-k scores into positive and negative example summaries.
- Reward-score generation expects the search output and writes a new score file for KD or reward training.
- KD training expects the released or generated score files under the data directory.

### Helpful config fields

From the distilled `Arguments` dataclass, the most common planning fields are:

- `model_name_or_path`
- `data_dir`
- `train_file`
- `search_split`
- `search_topk`
- `do_search`
- `do_kd_gen_score`
- `kd_gen_score_split`
- `kd_gen_score_batch_size`
- `do_kd_biencoder`
- `llm_model_name_or_path`
- `llm_k_shot`
- `llm_batch_size_per_device`
- `llm_max_input_length`
- `llm_max_decode_length`
- `llm_eval_split`
- `llm_eval_tasks`
- `topk_as_positive`
- `bottomk_as_negative`
- `held_out_tasks`

## CED-ICL plan fields

The distilled CED-ICL runner uses a compact config bundle. For planning, remember these fields from the public config:

- `batch_size`
- `eval_batch_size`
- `do_generation`
- `num_shot`
- `max_valid_size`
- `no_loss_reduce`
- `save_model`
- `do_icl`
- `do_ppl`

The experiment launcher also passes a configuration bundle name, a loaded checkpoint glob, an experiment name, random seeds, and a few-shot toggle. If you need to validate that a CED-ICL plan is sane, check the checkpoint root and the dataset identifier before adjusting the config stack.

## Structured Prompting / Understand ICL file expectations

### Structured Prompting

- Fairseq-style runs need a model checkpoint, architecture name, BPE encoder files, dictionary file, and output path.
- Hugging Face many-shot runs need a model root, task name, strategy, chunk count, and max length.

### Understand ICL

The record-generating run uses:

- `model_name`
- `model_arch`
- `task`
- `k`
- `seed`
- `perm_id`
- `output_path`
- `base_dir`
- `lr`

The analysis step expects record files under a base analysis directory. If the analysis helper still contains a placeholder base-dir string, patch it in a temporary copy before running the real analysis.

## Tiny plan examples

### UPRISE cross-task plan

```json
{
  "project": "uprise",
  "task_name": "copa",
  "metric": "simple_accuracy",
  "class_num": 2,
  "train_clusters": "train_example_1+train_example_2",
  "test_clusters": "test_example_1+test_example_2",
  "prompt_setup_type": "qa"
}
```

### SE2 sanity plan

```json
{
  "project": "se2",
  "task_name": "copa",
  "metric": "simple_accuracy",
  "class_num": 2,
  "beam_size": 3,
  "shot_num": 3,
  "score_cmd_name": "score.sh",
  "train_cmd_name": "train.sh",
  "infer_cmd_name": "infer.sh"
}
```

### LLM Retriever search plan

```json
{
  "project": "llm-retriever",
  "model_name_or_path": "intfloat/llm-retriever-base",
  "data_dir": "data/tasks",
  "search_split": "train",
  "search_topk": 100,
  "llm_model_name_or_path": "huggyllama/llama-7b"
}
```

Use these examples as shape references only. The bundled validator is the authoritative check for the generated sub-skill.
