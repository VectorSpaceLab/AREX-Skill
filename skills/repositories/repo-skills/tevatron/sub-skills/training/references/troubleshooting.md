# Training Troubleshooting

Use this reference to diagnose Tevatron training command plans before running long jobs.

## Optional Dependency Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'torch'` | Core Tevatron metadata does not install PyTorch. | Install the PyTorch build matching the user's CUDA/CPU/accelerator environment before training. |
| `ModuleNotFoundError: No module named 'peft'` | `--lora` or `--lora_name_or_path` requires PEFT. | Install `peft` and verify the selected adapter modules exist in the backbone. |
| DeepSpeed launcher or `--deepspeed` import fails | DeepSpeed is optional. | Install `deepspeed` for the exact Python/CUDA stack, or switch to `torchrun`/single-process training. |
| `Grad Cache package not available` | PyTorch GradCache trainer imports `grad_cache`. | Install the GradCache package or remove `--grad_cache`. |
| FlashAttention import/build failure | Default `--attn_implementation` is `flash_attention_2`, but `flash-attn` is optional and hardware-sensitive. | Use `--attn_implementation sdpa` or `--attn_implementation eager`, or install a compatible `flash-attn`. |
| JAX driver import errors for `jax`, `flax`, or `optax` | JAX stack is optional. | Install the accelerator-appropriate JAX stack and `flax`/`optax`, or use PyTorch training. |
| Tevax MP import errors for `magix` or `grad_cache.cachex` | Experimental Tevax route requires extra packages beyond core Tevatron. | Install and verify the Tevax/JAX dependencies, or use `tevatron.retriever.driver.jax_train` instead. |
| RepLLaMA example fails on `xformers` | Example replaces LLaMA attention with xFormers. | Install `xformers` compatible with the user's PyTorch/CUDA stack or adapt the example to current Transformers attention. |

Do not recommend broad dependency installation without checking the user's accelerator, CUDA, and Python constraints.

## Missing `--do_train`

Symptoms:

- A command parses but does not behave like a training run.
- Non-empty output-directory protection does not trigger.
- The user's command looks like a training command but only configures arguments.

Fix:

- Add `--do_train` for `tevatron.retriever.driver.train`, `train_distil`, `jax_train`, and example drivers built on Hugging Face `TrainingArguments`.
- Keep `--do_train` in generated command plans unless a user explicitly asks only for parser help or dry-run inspection.

## Output Directory, Resume, and Overwrite

Symptoms:

- `ValueError: Output directory (...) already exists and is not empty. Use --overwrite_output_dir to overcome.`
- Training silently resumes from a checkpoint the user did not intend to use.
- Checkpoints are overwritten or mixed with incompatible runs.

Cause:

- Dense and distillation drivers block non-empty output directories when `--do_train` is set and `--overwrite_output_dir` is absent.
- They call `get_last_checkpoint(output_dir)` and resume automatically when a checkpoint exists.

Fix:

- Fresh experiment: choose a new `--output_dir` or intentionally pass `--overwrite_output_dir`.
- Resume experiment: keep the existing checkpoint files and verify model/data/precision settings match the original run.
- Avoid reusing a directory across dense, distillation, sparse, and JAX routes.
- For SPLADE, UniCOIL, and RepLLaMA example drivers, do not promise automatic resume without reviewing the adapted driver; source comments mark resume as TODO in those examples.

## LoRA Module Mismatch

Symptoms:

- PEFT reports target modules not found.
- Training creates too few trainable parameters.
- Adapter loads but downstream encoding quality is poor after fine-tuning.

Cause:

- Default target modules are for many LLaMA/Mistral-style decoder blocks: `q_proj,k_proj,v_proj,o_proj,down_proj,up_proj,gate_proj`.
- BERT-like models, E5 variants, or custom architectures may use different module names.

Fix:

- Inspect the backbone module names before finalizing `--lora_target_modules`.
- For decoder-only LLM retrievers, preserve `--pooling eos` or `--pooling last`, `--append_eos_token`, and prefixes used during training and later encoding.
- Use `--lora_name_or_path` only when continuing from or loading a compatible adapter for the same base model family.

## OOM and Batch Planning

Symptoms:

- CUDA OOM before the first optimizer step.
- OOM during backward only.
- DeepSpeed ZeRO-0 fits small models but fails on LLM LoRA runs.
- JAX process exits from XLA allocation pressure.

Fix order:

1. Lower `--per_device_train_batch_size` or Tevax `--batch_size`.
2. Lower `--train_group_size` or Tevax `--num_target_passages`.
3. Lower `--query_max_len` and `--passage_max_len`; passages dominate memory because each query expands to `train_group_size` passages.
4. Enable `--gradient_checkpointing` for large PyTorch backbones.
5. Enable `--grad_cache` and reduce `--gc_q_chunk_size`/`--gc_p_chunk_size`.
6. Increase `--gradient_accumulation_steps` to keep effective batch size after reducing microbatch size.
7. Move from DeepSpeed ZeRO-0 to ZeRO-3 for large models.
8. Use BF16 on supported hardware, or FP16 when BF16 is unavailable and numerically stable.

Effective PyTorch examples:

- In-batch passages per GPU update scale as `per_device_train_batch_size * gradient_accumulation_steps * train_group_size` for one process.
- Distributed effective queries scale further by process count.
- GradCache chunk sizes control memory; they do not change the logical training group size.

## GradCache Chunk Sizing

Symptoms:

- GradCache still OOMs.
- GradCache fails due invalid chunk sizing.
- Training becomes unexpectedly slow.

Fix:

- Start with `gc_q_chunk_size` below or equal to `per_device_train_batch_size`.
- Start with `gc_p_chunk_size` below or equal to `per_device_train_batch_size * train_group_size`.
- Reduce passage chunk size first when passage encoding dominates memory.
- Avoid extremely tiny chunks unless necessary; they increase forward-pass overhead.
- On JAX HF-style driver, make sure chunk sizes divide the computed global query and passage batch counts well enough to avoid zero subbatch counts.

## Sequence Length and Padding

Symptoms:

- Shape or performance problems in attention kernels.
- Decoder-only retriever quality regresses after training.
- JAX GPU warnings or TransformerEngine issues.

Fix:

- Keep `--query_max_len` and `--passage_max_len` consistent between training and later encoding.
- Use `--append_eos_token` for decoder-only LLM retrievers that pool on EOS/last token.
- Default `--pad_to_multiple_of` is `16`, useful for tensor cores.
- For JAX GPU with TransformerEngine, use query and passage lengths that are multiples of `64`.
- If FlashAttention is unavailable, set `--attn_implementation sdpa` or `eager` instead of leaving the default `flash_attention_2`.

## Distillation Data Errors

Symptoms:

- Tensor conversion fails in `DistilTrainCollator`.
- KL loss gets NaNs or nonsensical labels.
- Missing `score` errors appear for selected passages.

Cause:

- Distillation expects numeric teacher scores for the exact selected positive and negative documents.
- Inline layout checks `score` on each positive/negative passage.
- ID-to-corpus layout resolves document IDs through the corpus and reads each document's `score`.

Fix:

- Validate a few rows before training: query, one selected positive, enough negatives, and numeric `score` values.
- Ensure `train_group_size - 1` negatives exist or accept sampling with replacement.
- Match `--corpus_name`/`--corpus_path` and `--corpus_split` to the ID namespace in the train file.
- Keep `--distil_temperature` separate from `--temperature`.

## Sparse Driver Pitfalls

Symptoms:

- `python -m tevatron.retriever.driver.train_splade` fails.
- UniCOIL command rejects `--train_n_passages`, `--q_max_len`, or `--p_max_len`.
- Sparse training runs but indexing/search later fails.

Cause:

- SPLADE and UniCOIL training are example-owned patterns, not installed package CLI modules.
- UniCOIL README uses older argument names.
- Encoding/search/indexing are separate workflows and may need Pyserini or other packages.

Fix:

- Adapt or copy the SPLADE example driver when training SPLADE; the package provides `SpladeModel` and the example provides FLOPS regularization.
- Translate old UniCOIL flags to current shared names when adapting the driver.
- Keep sparse encoding/indexing out of the training command review unless the user explicitly asks for the downstream retrieval workflow.

## TPU/JAX Gaps

Symptoms:

- `tevatron.driver.jax_train` fails but `tevatron.retriever.driver.jax_train` exists.
- `mesh_shape`, `model_type`, or checkpoint arguments are rejected.
- GradCache import differs between PyTorch and JAX routes.

Fix:

- Use `tevatron.retriever.driver.jax_train` for the current HF-style JAX driver.
- Use `tevatron.tevax.experimental.mp.train` or `train_lora` for experimental Tevax MP commands.
- Do not mix HF-style names (`output_dir`, `dataset_name`, `per_device_train_batch_size`) with Tevax MP names (`checkpoint_dir`, `train_file`, `batch_size`).
- Install the JAX stack for the target accelerator and verify `jax.device_count()` before planning batch sizes.

## Safe Command Review Checklist

Before approving a command:

- It prints or plans the command unless the user explicitly asked to launch training.
- The driver matches the route: dense, distil, SPLADE, UniCOIL adaptation, JAX, or Tevax.
- Data schema and `train_group_size` have enough positives/negatives and scores when needed.
- Optional dependencies are named as prerequisites, not assumed.
- Output directory behavior is intentional: fresh, overwrite, or resume.
- Memory plan matches hardware: batch size, group size, sequence lengths, GradCache, DeepSpeed, precision, and gradient checkpointing.
