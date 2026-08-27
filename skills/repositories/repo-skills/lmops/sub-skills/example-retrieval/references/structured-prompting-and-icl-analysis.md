# Structured Prompting and ICL analysis

Source-script labels in this reference identify upstream workflow concepts only. Use bundled planning/checking guidance from this generated skill before turning any label into a checkout-specific command.

Use this reference when the user needs many-shot prompting, structured prompt layouts, or in-context-learning analysis rather than retriever training.

## Structured Prompting: Fairseq-style workflow

The Fairseq-style path uses chunked demonstration groups and dense model checkpoints.

### Key command concept

```bash
source-script-label:manyshot.sh <seed> <task> <model_path> <model_arch> <k> <chunk_len> <batch_size> <ngpu> <bpe_path> <encoder_path> <dict_path> <output_path>
```

### Important knobs

- `seed`: chooses a specific demonstration permutation; the workflow typically reports averages over several seeds.
- `task`: task name from the structured-prompting task registry; the public workflow lists many classification and generation tasks.
- `model_path`: dense model checkpoint directory.
- `model_arch`: architecture family such as the GPT-like dense model variants used by the workflow.
- `k`: number of demonstrations.
- `chunk_len`: per-chunk token length used to pack example groups.
- `batch_size`: inference batch size.
- `ngpu`: number of GPUs available on the node.
- `bpe_path`, `encoder_path`, `dict_path`: tokenizer and dictionary assets.
- `output_path`: destination for the result files.

### Layout and alignment notes

- The default alignment strategy truncates each group to a fixed length.
- Some variants can use space padding instead of truncation.
- If neither is chosen, the workflow falls back to attention-mask style alignment.
- The Fairseq-style path expects old-model and old-library compatibility, so treat dependency mismatches as a normal troubleshooting branch rather than as a sign that the workflow is wrong.

## Structured Prompting: Hugging Face variant

The Hugging Face variant is a smaller evaluation entry point that focuses on many-shot inference.

### Key command concept

```bash
python3 eval_many.py \
  --model bloom \
  --dtype float16 \
  --parallel \
  --task sst2 \
  --strategy truncate \
  --data_path <model-root> \
  --chunk_num 5 \
  --max_length 2000
```

### Important knobs

- `model`: model family name.
- `dtype`: numeric precision; `int8` changes the path through the evaluator.
- `parallel`: activate model parallelism when supported.
- `task`: dataset name from the dataset registry.
- `strategy`: alignment strategy such as truncation.
- `data_path`: directory containing the model assets.
- `chunk_num`: desired chunk count for the many-shot prompt.
- `shot`: optional number of shots.
- `repeat_num`: number of seeds or repetitions.
- `max_length`: total sequence length budget.
- `log_path`: optional JSON log output.

The Hugging Face path is useful when a user wants a many-shot static recipe without full Fairseq orchestration.

## Understand ICL analysis

Understand ICL is a two-step analysis pipeline that records internal behavior under several settings and then analyzes the record files.

### Step 1: record generation

The run script takes these positions:

- `model_name`
- `model_arch`
- `task`
- `k`
- `seed`
- `perm_id`
- `output_path`
- `base_dir`
- `lr`

It then prepares three settings plus a finetuning baseline:

- `ft`: train a small finetuned model for analysis.
- `ftzs`: evaluate the finetuned model in zero-shot mode.
- `zs`: evaluate the base model in zero-shot mode.
- `icl`: evaluate the base model with in-context examples.

The script writes `record_info.jsonl` files under a base analysis directory. The downstream analysis depends on those record files being present for all desired model/task combinations.

### Step 2: analysis

The analysis script computes similarity and attention statistics from the recorded files and writes JSON summaries. It iterates over tasks such as `cb`, `sst2`, `sst5`, `subj`, `mr`, and `agnews`, and over the model sizes recorded by the public workflow.

### Important caution

The analysis scripts in the source workflow embed placeholder base-directory text in the analysis helpers. A future agent should patch the placeholder or route through a bundled wrapper before running the real analysis. Do not assume the public script can be run unchanged in a fresh checkout.

## Troubleshooting focus for this family

- Old Fairseq, Transformers, or bitsandbytes versions can be required by the structured-prompting stack.
- Missing BPE or dictionary files usually show up as path errors before model loading.
- Many-shot evaluation can exceed the context window; check `k`, `chunk_len`, and `max_length` before blaming the model.
- For Understand ICL, check that the analysis-record files exist before running the analysis pass.
- If you need a command template or stage reminder, use `../scripts/build_retrieval_commands.py` only for retrieval-family workflows and keep structured-prompting / Understand ICL orchestration separate.
