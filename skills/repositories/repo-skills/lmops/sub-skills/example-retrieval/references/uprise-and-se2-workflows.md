# UPRISE and SE2 workflows

This reference covers LMOps workflows where the main problem is choosing examples or prompts for in-context learning. Use the bundled planner `../scripts/build_retrieval_commands.py` to produce safe command templates before attempting any source workflow.

## Choosing UPRISE vs SE2

| User intent | Prefer | Why |
| --- | --- | --- |
| Universal prompt retrieval across task families or models | UPRISE | Trains a lightweight retriever on scored prompts and applies it to unseen task clusters or different inference LLMs. |
| Task-specific few-shot demonstration retrieval | UPRISE or SE2 | UPRISE can be run task-specific by training and testing on the same task; SE2 adds sequential awareness and beam search for ordered example sequences. |
| Sequential example selection with score/train/infer stages | SE2 | SE2 scores multi-step candidate sequences, merges scored data, trains a sequential-aware DPR-style retriever, and performs beam-search retrieval. |
| BM25/SBERT/random ablation around prompt pools | UPRISE or SE2 | Both command generators expose random, BM25, and SBERT alternatives to the learned retriever. |
| Prompt rewriting or text-to-image prompt optimization | Not this sub-skill | Route to `../prompt-optimization/SKILL.md`. |
| CoRAG/LLMA RAG or decoding acceleration | Not this sub-skill | Route to `../rag-and-acceleration/SKILL.md`. |

## UPRISE operating flow

UPRISE has two common flows: evaluating an existing retriever/prompt pool, or training a custom retriever.

### A. Existing retriever and prompt pool

1. Stage the retriever checkpoint, prompt-pool JSON, model/dataset cache, and output directory.
2. Encode the prompt pool with the prompt encoder. The command concept contains:
   - `model_file=<retriever checkpoint>`
   - `ctx_src=dpr_uprise`, `shard_id=0`, `num_shards=1`
   - `out_file=<experiment output>/dpr_enc_index`
   - `ctx_sources.dpr_uprise.prompt_pool_path=<prompt pool>`
   - `ctx_sources.dpr_uprise.prompt_setup_type=qa` for cross-task prompt retrieval, or `q` for task-specific question-only setup.
   - `encoder.cache_dir=<cache>` and `hydra.run.dir=<experiment output>`.
3. Define or select the test task and metric. UPRISE task classes must agree with a metric name understood by the metric function dispatcher. Use `../scripts/validate_task_metric_plan.py` on a tiny JSON plan before editing task code.
4. Run inference through a Hugging Face model path or an OpenAI engine path. The HF path needs model downloads/cache and GPU memory appropriate to the chosen LLM. The OpenAI path needs an OpenAI token in the environment and was originally exercised for GPT-3-style engines; verify current client compatibility before using a newer chat model.
5. Record the prediction file, result file, task name, model name, prompt file, prompt count, and cache used for the run.

### B. Training and evaluating a custom UPRISE retriever

1. Add or confirm task definitions, metric mapping, train cluster map, and test cluster map.
2. Use `../scripts/build_retrieval_commands.py --project uprise ...` to print the top-level command-generator template. The distilled get-command flags are:
   - Output/cache/hardware: `--output_dir`, `--cache_dir`, `--gpus`.
   - Training clusters and scoring: `--train_clusters`, `--retriever_prompt_setup`, `--ds_size`, `--scr_model`, `--multi_task`.
   - Retriever training: `--retriever_top_k`, `--retriever_bsz`, `--retriever_epoch`.
   - Inference and ablations: `--inf_model`, `--test_clusters`, `--num_prompts`, `--retrieve_random`, `--retrieve_bm25`, `--retrieve_sbert`, `--inference_bsz`.
3. The command generator writes a training script and an inference script under an experiment directory named from the train/test cluster strings. Treat those generated scripts as the source workflow's heavy artifacts; inspect before running.
4. Training script stage order:
   - Build prompt-pool JSON and random sampled prompt IDs for every training task.
   - Score sampled prompt candidates with the scoring LLM.
   - Train the DPR-style dense prompt retriever using scored train/valid data.
5. Inference script stage order:
   - Encode the prompt pool with the trained retriever checkpoint.
   - Retrieve prompts for every test task using the learned retriever.
   - Run zero-shot and retrieved-prompt inference.
   - Optionally run random, BM25, and SBERT baselines.
6. For task-specific few-shot retrieval, train and test on matching task clusters and do not set multi-task unless the task plan intentionally mixes tasks.
7. For chain-of-thought prompts, treat the CoT task as a text-completion task with a task-specific metric. Confirm that generated CoT demonstrations are present in the prompt pool before scoring.

## SE2 operating flow

SE2 has an explicit three-stage pipeline: Scoring, Training, Inference. A COPA run is the smallest documented walk-through, but even that can take around an hour on eight V100-32GB GPUs. Do not present CPU static checks as proof of the full SE2 result.

### Stage 0: command generation

Use `../scripts/build_retrieval_commands.py --project se2 ...` to print the top-level command-generator template. Distilled flags are:

- Output/cache/hardware: `--output_dir`, `--cache_dir`, `--gpus`.
- Generated script names and checkpoint folder: `--score_cmd_name`, `--train_cmd_name`, `--infer_cmd_name`, `--model_folder`.
- Scoring/training: `--train_clusters`, `--retriever_prompt_setup`, `--infer_prompt_setup`, `--ds_size`, `--scr_model`, `--multi_task`, `--retriever_top_k`, `--retriever_bsz`, `--retriever_epoch`.
- Inference: `--inf_model`, `--test_clusters`, `--beam_size`, `--shot_num`, `--retrieve_random`, `--retrieve_bm25`, `--retrieve_sbert`, `--inference_bsz`.

SE2 usually uses a single task as both train and test cluster. The task list documented by the workflow includes `copa`, `arc_c`, `arc_e`, `openbookqa`, `mrpc`, `qqp`, `paws`, `mnli`, `qnli`, `snli`, `rte`, `sst2`, `sst5`, `sentiment140`, `hellaswag`, `ag_news`, `roc_story`, `roc_ending`, `gigaword`, `aeslc`, `common_gen`, and `e2e_nlg`.

### Stage 1: scoring

The generated score script performs these operations:

1. Create a prompt pool from the task train split.
2. Sample step-1 candidate prompt IDs for each input.
3. Score step-1 candidates with the scoring LLM.
4. Sample step-2 candidates conditioned on high-ranked step-1 choices.
5. Score step-2 candidates.
6. Sample step-3 candidates conditioned on previous choices.
7. Score step-3 candidates.
8. Merge step-1/2/3 train and valid scored files into final train/valid scored data.

Shortcut: if a compatible scored-data bundle is already staged, the user may skip scoring and start at training. The staged files must match the generated paths or the generated training command must be edited deliberately.

### Stage 2: training

The generated train script trains a DPR-style sequential retriever with `se2_dataset` and `se2_valid_dataset`. It uses the task-specific learning rate when present in the task class. Required inputs include the merged scored train/valid JSON files, the prompt pool, train cluster string, prompt setup, cache directory, hard-negative top-k, batch size, and epoch count.

Shortcut: if a compatible trained checkpoint is already staged, the user may skip training and start at inference. The expected checkpoint name is `dpr_biencoder.best_valid` under the model folder selected during command generation, unless the inference command is deliberately edited.

### Stage 3: inference

The generated inference script performs:

1. Encode the prompt pool using the trained sequential retriever.
2. Retrieve candidate prompt sequences with beam search. Important knobs are `beam_size` and `shot_num`.
3. Run inference with the inference LLM.
4. Optionally run random, BM25, and SBERT baselines.

SE2's own inference reader handles ordered prompt sequences and can test alternative orderings. If a user asks about ordering permutations, treat it as an inference-analysis concern and do not rerun scoring unless the scored data itself is stale.

## Safe planning examples

Print a UPRISE cross-task plan with BM25 ablation:

```bash
python ../scripts/build_retrieval_commands.py \
  --project uprise \
  --train-clusters train_example_1+train_example_2 \
  --test-clusters test_example_1+test_example_2 \
  --score-model EleutherAI/gpt-neo-2.7B \
  --infer-model EleutherAI/gpt-neo-2.7B \
  --retrieve-bm25
```

Print a SE2 COPA plan with generated script names:

```bash
python ../scripts/build_retrieval_commands.py \
  --project se2 \
  --train-clusters copa \
  --test-clusters copa \
  --score-model EleutherAI/gpt-neo-2.7B \
  --infer-model EleutherAI/gpt-neo-2.7B \
  --beam-size 3 \
  --shot-num 3
```

These examples print templates only. They do not download data, load models, score prompts, train retrievers, or launch inference.
