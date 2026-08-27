# LLM Retriever and CED-ICL workflows

This reference covers the workflows where example selection is trained from model feedback or demonstration scoring. Use the bundled planner `../scripts/build_retrieval_commands.py` before any heavy source workflow.

## LLM Retriever at a glance

LLM Retriever learns a dense retriever for in-context example selection by combining three ideas:

1. Format a shared task corpus into prompt-ready JSONL files.
2. Train or reuse a reward model that scores candidate demonstrations with LLM feedback.
3. Distill those scores into a bi-encoder retriever and search the prompt corpus.

### Data files and shapes

The bundled data-format reference describes the exact field shapes, but the main files are:

- `passages.jsonl.gz`: each row contains `id`, `contents`, and `task_name`.
- `train.jsonl.gz` / `test.jsonl.gz`: each row contains `query_id`, `query`, `answers`, `options`, and `task_name`.
- `bm25_train.jsonl.gz`, `kd_bm25_train.jsonl.gz`, and `kd_it2_train.jsonl.gz`: released training or reward-score files.
- Search and scoring outputs add `doc_ids`, `doc_scores`, and readable positive/negative summaries.

The task formatter script uses task definitions to build these files. The formatter can truncate the training portion per task, which is useful for small local sanity checks.

### Key command concepts

- Data download: fetch the released preprocessed task bundle before any training or evaluation.
- Data formatting: convert the original task layout into the codebase layout with the bundled formatter.
- Released checkpoint evaluation: load the retriever checkpoint and run evaluation over the chosen split.
- Reward-score generation: score BM25 candidates with an LLM, then train a reward model from the generated score file.
- KD bi-encoder training: train the dense retriever from released reward scores or from your own scores.
- Search top-k: retrieve a new candidate set with a trained retriever, then iterate the reward-score and retriever-training cycle.

### Safe command-plan sequence

Use the planner to print the stage order and command concepts only:

```bash
python ../scripts/build_retrieval_commands.py \
  --project llm-retriever \
  --stage all \
  --data-dir <data-root> \
  --output-dir <output-root> \
  --llm-model huggyllama/llama-7b \
  --retriever-model intfloat/llm-retriever-base
```

A typical full loop is:

1. `download-data`
2. `format-data`
3. `eval-retriever` or `train-kd-biencoder`
4. `gen-llm-score`
5. `train-reward`
6. `search-topk`
7. `gen-reward-scores`
8. repeat the KD cycle if needed

Do not treat the planner as a downloader or training launcher. It prints what a later agent should run.

## LLM Retriever configuration notes

The `Arguments` dataclass in the source workflow exposes these important families of fields:

- Model and data: `model_name_or_path`, `data_dir`, `train_file`, `train_n_passages`, `max_len`, `reward_max_length`.
- Search: `do_search`, `search_split`, `search_batch_size`, `search_topk`.
- KD scoring and training: `do_kd_gen_score`, `kd_gen_score_split`, `kd_gen_score_batch_size`, `do_kd_biencoder`, `kd_cont_loss_weight`.
- Evaluation: `do_llm_eval`, `llm_model_name_or_path`, `llm_k_shot`, `llm_batch_size_per_device`, `llm_max_input_length`, `llm_max_decode_length`, `llm_eval_split`, `llm_eval_tasks`, `llm_constrained_decoding`.
- Data selection helpers: `topk_as_positive`, `bottomk_as_negative`, `held_out_tasks`, `pool_type`, `add_qd_prompt`, `l2_normalize`, `full_contrastive_loss`.

If a user needs to validate a tiny plan file before editing command arguments, use `../scripts/validate_task_metric_plan.py` to check task names, metrics, and a few shape fields without importing source code.

## LLM Retriever evaluation and iterative training

- Evaluation of the released checkpoint uses the evaluation script with an output directory and the checkpoint identifier.
- Training from released reward scores uses the KD bi-encoder training script with the released score files already staged under the data directory.
- Generating LLM feedback scores with LLaMA-7B uses the score-generation script over BM25 candidates. The workflow expects GPU memory and model downloads.
- Reward-model training uses the generated LLM score file.
- Iterative training uses `search_topk` to refresh the candidate set, then repeats the scoring and training cycle.

The dense retriever path needs the same task formatting conventions as the formatter and evaluation code. In particular, the query, answers, options, and task name columns must stay consistent across all derived files.

## CED-ICL at a glance

CED-ICL is a related demonstration-selection workflow that ranks in-context examples by cross-entropy difference. It uses a public T-Few-based stack and a compact experiment runner.

### What the runner does

The runner script groups these phases:

- Install the CED-ICL environment requirements into a workspace named `cdsicd`.
- Run one-shot in-domain model preparation.
- Compute CED scores for each model/task pair.
- Optionally compute training-data CED scores for in-domain PEFT model training.
- Build clustered CED scorers.
- Compute clustered CED scores.

### CED-ICL command concepts

The experiment launcher accepts small positional arguments for GPU id, dataset index, start, and end. The underlying evaluation script uses a T-Few-style config bundle and writes experiment logs, record files, and final outputs into the selected experiment directory.

The bundled planner does not launch these runs. Use the reference only to understand stage order, dependency style, and expected output roots.

## Troubleshooting focus for this family

- Check that the task formatter produced the shared JSONL files before retriever training.
- Check that the reward-score file exists before reward-model training.
- Check that the retriever checkpoint path is the one that the evaluator or search script expects.
- Expect GPU memory pressure for `gen_llm_score`, reward training, and dense-retriever training.
- Expect T-Few and PEFT dependencies for CED-ICL, plus a separate runtime workspace and experiment runner.
- If search or evaluation looks like it is reading the wrong file, verify the output directory and the staged data filename suffixes first.
