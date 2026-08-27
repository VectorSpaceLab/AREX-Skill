# Training Workflows

This reference distills Tevatron training commands into reusable patterns. The commands are examples to adapt; they may download models/datasets and run long GPU or TPU jobs if executed.

## Dense PyTorch Retriever

Use the main dense driver for normal bi-encoder retriever training:

```bash
python -m tevatron.retriever.driver.train \
  --do_train \
  --output_dir model_nq \
  --dataset_name Tevatron/wikipedia-nq \
  --model_name_or_path bert-base-uncased \
  --save_steps 20000 \
  --fp16 \
  --per_device_train_batch_size 32 \
  --train_group_size 2 \
  --learning_rate 1e-5 \
  --query_max_len 32 \
  --passage_max_len 156 \
  --num_train_epochs 40
```

Validation checkpoints:

- The driver is `tevatron.retriever.driver.train` and uses `DenseModel`, `TrainDataset`, and `TrainCollator`.
- `--do_train` must be present; otherwise Hugging Face training arguments do not mark the run as training.
- `--train_group_size` is the number of passages per query: one positive plus `train_group_size - 1` negatives.
- `--temperature` scales contrastive logits; defaults to `1.0` but LLM retriever examples often use `0.01`.
- `--pooling` defaults to `cls`; supported dense pooling names are `cls`, `first`, `mean`, `avg`, `average`, `last`, and `eos`.
- `--normalize` L2-normalizes query and passage vectors after pooling.

Use `torchrun --nproc_per_node=N -m tevatron.retriever.driver.train ...` for distributed PyTorch without DeepSpeed. Use `deepspeed --module tevatron.retriever.driver.train ...` when passing `--deepspeed`.

## Local JSON or JSONL Training

Tevatron's `DataArguments` default `dataset_name` is `json`, so local JSON/JSONL can be loaded with `--dataset_path`:

```bash
python -m tevatron.retriever.driver.train \
  --do_train \
  --output_dir model_local \
  --dataset_name json \
  --dataset_path train.jsonl \
  --model_name_or_path bert-base-uncased \
  --per_device_train_batch_size 8 \
  --train_group_size 4 \
  --learning_rate 1e-5 \
  --query_max_len 32 \
  --passage_max_len 128 \
  --num_train_epochs 1
```

Accepted training layouts:

- Legacy inline text layout: each row has `query`, `positive_passages`, and `negative_passages`; each passage has `text` and optional `title`.
- ID-to-corpus layout: each row has `query_id`, `query_text`, `positive_document_ids`, and `negative_document_ids`; pair it with `--corpus_name`/`--corpus_path` so IDs resolve to documents with `docid` and `text`.
- Distillation layout: same as above, but every positive and negative passage/document must expose a numeric `score`.

If using multiple local files through `datasets.load_dataset('json')`, pass a data file or directory that Hugging Face Datasets can resolve for the selected `--dataset_split`.

## GradCache

Enable GradCache to increase effective batch size on limited memory:

```bash
CUDA_VISIBLE_DEVICES=0 python -m tevatron.retriever.driver.train \
  --do_train \
  --output_dir model_nq_gc \
  --dataset_name Tevatron/wikipedia-nq \
  --model_name_or_path bert-base-uncased \
  --fp16 \
  --per_device_train_batch_size 128 \
  --train_group_size 2 \
  --learning_rate 1e-5 \
  --query_max_len 32 \
  --passage_max_len 156 \
  --num_train_epochs 40 \
  --grad_cache \
  --gc_q_chunk_size 32 \
  --gc_p_chunk_size 16
```

Operational notes:

- `--grad_cache` switches the trainer class from `TevatronTrainer` to `GradCacheTrainer`.
- PyTorch GradCache imports the optional `grad_cache` package and raises a clear error if it is missing.
- `--gc_q_chunk_size` and `--gc_p_chunk_size` are per-chunk tensor batch sizes; reduce them when OOM persists.
- Keep `gc_q_chunk_size <= per_device_train_batch_size` and `gc_p_chunk_size <= per_device_train_batch_size * train_group_size`.
- For JAX driver GradCache, Tevatron computes query subbatches as `train_batch_size // gc_q_chunk_size` and passage subbatches as `train_batch_size * train_group_size // gc_p_chunk_size`, so choose divisors that do not round to zero.

## LoRA LLM Retriever

Use LoRA when fine-tuning large decoder or embedding models without updating every weight. A representative DeepSpeed command is:

```bash
deepspeed --include localhost:0,1,2,3 --master_port 60000 --module tevatron.retriever.driver.train \
  --deepspeed ds_zero3_config.json \
  --do_train \
  --output_dir retriever-mistral \
  --model_name_or_path mistralai/Mistral-7B-v0.1 \
  --lora \
  --lora_target_modules q_proj,k_proj,v_proj,o_proj,down_proj,up_proj,gate_proj \
  --dataset_name Tevatron/msmarco-passage-aug \
  --query_prefix "Query: " \
  --passage_prefix "Passage: " \
  --bf16 \
  --pooling eos \
  --append_eos_token \
  --normalize \
  --temperature 0.01 \
  --per_device_train_batch_size 8 \
  --gradient_checkpointing \
  --train_group_size 16 \
  --learning_rate 1e-4 \
  --query_max_len 32 \
  --passage_max_len 156 \
  --num_train_epochs 1 \
  --logging_steps 10 \
  --overwrite_output_dir \
  --gradient_accumulation_steps 4
```

LoRA validation checkpoints:

- `--lora` constructs a PEFT LoRA adapter; `--lora_name_or_path` resumes or continues from an existing adapter.
- Default target modules are `q_proj,k_proj,v_proj,o_proj,down_proj,up_proj,gate_proj`; verify these names exist in the selected backbone.
- `--gradient_checkpointing` causes Tevatron to call `enable_input_require_grads()` before wrapping with LoRA.
- Decoder-only retrievers usually need `--pooling eos` or `--pooling last`, `--append_eos_token`, right padding, and explicit query/passage prefixes.
- `peft` is optional; core Tevatron metadata does not install it.

## DeepSpeed Config Choice

Tevatron examples use compact DeepSpeed JSON configs with automatic optimizer, scheduler, gradient accumulation, and train batch settings. Distill the configs into local files before running; do not rely on a source checkout path.

Use ZeRO-0 when:

- The model fits in GPU memory with normal data parallelism.
- You mainly want DeepSpeed launch, mixed precision, and automatic batch metadata.
- Debugging simplicity matters more than sharding.

Use ZeRO-3 when:

- Training a large LLM retriever or LoRA run that is OOM under ZeRO-0.
- You need parameter partitioning across GPUs.
- You can tolerate more communication and checkpoint complexity.

Both observed configs set `offload_optimizer.device` and `offload_param.device` to `none`, use `AdamW` with `torch_adam: true`, and let Hugging Face/DeepSpeed fill learning-rate, scheduler, gradient clipping, accumulation, and batch sizes through `auto` values.

## Teacher Distillation

Use `tevatron.retriever.driver.train_distil` when passage labels come from a teacher reranker:

```bash
deepspeed --include localhost:0,1,2,3 --master_port 60000 --module tevatron.retriever.driver.train_distil \
  --deepspeed ds_zero0_or_zero3_config.json \
  --do_train \
  --output_dir e5-base-distilled \
  --model_name_or_path intfloat/e5-base-unsupervised \
  --dataset_name rlhn/default-680K-bge-reranker-v2-gemma \
  --attn_implementation eager \
  --query_prefix "query: " \
  --passage_prefix "passage: " \
  --bf16 \
  --pooling mean \
  --normalize \
  --temperature 0.01 \
  --distil_temperature 0.02 \
  --per_device_train_batch_size 16 \
  --gradient_checkpointing \
  --train_group_size 16 \
  --learning_rate 2e-5 \
  --query_max_len 350 \
  --passage_max_len 350 \
  --num_train_epochs 5 \
  --logging_steps 5 \
  --overwrite_output_dir \
  --gradient_accumulation_steps 4
```

Distillation validation checkpoints:

- The driver uses `DistilTrainDataset`, `DistilTrainCollator`, and `DistilTevatronTrainer`.
- Every positive and negative passage in inline datasets needs a numeric `score` field.
- ID-to-corpus distillation requires corpus documents with `docid` and `score`; missing scores propagate into the collated teacher-label tensor and will fail.
- `--distil_temperature` defaults to `0.02` and is separate from the dense model's contrastive `--temperature`.
- The trainer gathers teacher labels in DDP before computing KL divergence against student scores.

## SPLADE Sparse Training

SPLADE uses `SpladeModel` from `tevatron.retriever.modeling.splade` and an example driver that adds FLOPS regularization:

```bash
CUDA_VISIBLE_DEVICES=0 python train_splade.py \
  --output_dir model_msmarco_splade \
  --model_name_or_path Luyu/co-condenser-marco \
  --save_steps 20000 \
  --dataset_name Tevatron/msmarco-passage-aug \
  --fp16 \
  --per_device_train_batch_size 32 \
  --train_group_size 8 \
  --learning_rate 5e-6 \
  --query_max_len 128 \
  --passage_max_len 128 \
  --q_flops_loss_factor 0.01 \
  --p_flops_loss_factor 0.01 \
  --num_train_epochs 3 \
  --dataloader_num_workers 8 \
  --num_proc 8 \
  --logging_steps 500 \
  --attn_implementation sdpa \
  --overwrite_output_dir
```

Because `train_splade.py` is an example script, copy or adapt that driver into the user's project before relying on this exact command in a different working directory. The package does include `SpladeModel`, but it does not expose a dedicated installed module like `tevatron.retriever.driver.train_splade`.

## UniCOIL Sparse Training

UniCOIL evidence comes from an example driver and README using older Tevatron option names. The current package exposes `UniCoilModel` in `tevatron.retriever.modeling.unicoil`, but the example driver imports legacy modules and should be treated as an adaptation starting point rather than a directly runnable installed-package command.

Original pattern to adapt:

```bash
CUDA_VISIBLE_DEVICES=0 python train_unicoil.py \
  --output_dir unicoil_distilbert \
  --model_name_or_path distilbert-base-uncased \
  --save_steps 20000 \
  --dataset_name Tevatron/msmarco-passage \
  --fp16 \
  --per_device_train_batch_size 8 \
  --train_n_passages 8 \
  --learning_rate 5e-6 \
  --q_max_len 16 \
  --p_max_len 128 \
  --num_train_epochs 3 \
  --add_pooler \
  --projection_in_dim 768 \
  --projection_out_dim 1 \
  --logging_steps 500 \
  --overwrite_output_dir
```

When adapting to current arguments, translate:

- `--train_n_passages` to `--train_group_size`.
- `--q_max_len` to `--query_max_len`.
- `--p_max_len` to `--passage_max_len`.
- Legacy imports such as `tevatron.data`, `tevatron.modeling`, and `tevatron.datasets` to the current `tevatron.retriever.*` package layout.

The bundled command builder's `--route unicoil` emits the translated command skeleton for an adapted `train_unicoil.py`; it does not supply the driver implementation.

## RepLLaMA-Style Training

RepLLaMA training is example-owned and uses local files in its example directory plus xFormers attention replacement. Treat it as a specialized adaptation, not a package-level driver:

```bash
deepspeed --include localhost:0,1,2,3 train.py \
  --deepspeed ds_zero3_config.json \
  --do_train \
  --output_dir model_repllama \
  --model_name_or_path meta-llama/Llama-2-7b-hf \
  --bf16 \
  --per_device_train_batch_size 8 \
  --gradient_accumulation_steps 4 \
  --gradient_checkpointing \
  --train_group_size 16 \
  --learning_rate 1e-4 \
  --query_max_len 32 \
  --passage_max_len 196 \
  --num_train_epochs 1 \
  --logging_steps 10 \
  --overwrite_output_dir \
  --num_proc 32 \
  --warmup_steps 100
```

The README uses older names (`train_n_passages`, `q_max_len`, `p_max_len`, `dataset_proc_num`, `negatives_x_device`); the current shared arguments use `train_group_size`, `query_max_len`, `passage_max_len`, and `num_proc`.

## JAX and Tevax Routes

Current HF-style JAX driver:

```bash
python -m tevatron.retriever.driver.jax_train \
  --do_train \
  --output_dir model_nq_jax \
  --dataset_name Tevatron/wikipedia-nq \
  --model_name_or_path bert-base-uncased \
  --per_device_train_batch_size 16 \
  --train_group_size 2 \
  --learning_rate 1e-5 \
  --query_max_len 32 \
  --passage_max_len 156 \
  --num_train_epochs 40
```

Experimental Tevax LoRA route:

```bash
python -m tevatron.tevax.experimental.mp.train_lora \
  --checkpoint_dir retriever-mistral-jax \
  --train_file Tevatron/msmarco-passage-aug \
  --model_name mistralai/Mistral-7B-v0.1 \
  --model_type mistral \
  --batch_size 128 \
  --num_target_passages 16 \
  --learning_rate 1e-4 \
  --mesh_shape 1 -1 \
  --weight_decay 0.00001 \
  --num_epochs 1 \
  --max_query_length 64 \
  --max_passage_length 128 \
  --pooling eos \
  --scale_by_dim True \
  --grad_cache \
  --passage_num_chunks 32 \
  --query_num_chunks 4
```

JAX validation checkpoints:

- Optional packages include `jax`, `flax`, `optax`, `magix`, and `grad_cache`; they are not Tevatron core dependencies.
- `tevatron.retriever.driver.jax_train` saves either one tied encoder or `query_encoder`/`passage_encoder` when `--untie_encoder` is used.
- `tevatron.tevax.experimental.mp.train_lora` uses `checkpoint_dir`, `train_file`, `batch_size`, and `num_target_passages` instead of the HF-style `output_dir`, `dataset_name`, `per_device_train_batch_size`, and `train_group_size` names.
- For JAX GPU with TransformerEngine, keep query and passage lengths multiples of 64 and consider `XLA_PYTHON_CLIENT_MEM_FRACTION=.95`.

## Checkpoint and Output Behavior

PyTorch dense and distillation drivers check for a non-empty `--output_dir` only when `--do_train` is set. If the directory is non-empty and `--overwrite_output_dir` is absent, they raise an error. They also call `get_last_checkpoint(output_dir)` and pass `resume_from_checkpoint=True` when a checkpoint exists.

Implications:

- For a deliberate fresh run, use a new output directory or `--overwrite_output_dir`.
- For a deliberate resume, keep the checkpoint directory intact and do not delete trainer state.
- For SPLADE, UniCOIL, and RepLLaMA example drivers, source comments indicate resume support is not fully implemented, so do not promise automatic resume without verifying the adapted driver.
