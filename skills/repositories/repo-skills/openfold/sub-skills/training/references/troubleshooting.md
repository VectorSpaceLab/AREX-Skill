# Training Troubleshooting

## CLI Help or Import Fails Before Argument Parsing

Symptom: `python train_openfold.py --help` fails while importing OpenFold modules, often with a missing compiled extension such as `attn_core_inplace_cuda`.

Recovery:

- Treat this as an environment/install problem, not a training-argument problem.
- Route CUDA/PyTorch/extension repair to `../installation-assets/`.
- Use the bundled dry-run command builders because they do not import OpenFold.
- Do not claim full CLI execution was verified until the target environment imports the training script successfully.

## Missing Caches, Indexes, or Alignment Files

Symptoms include missing JSON cache errors, alignment lookup failures, template date failures, or a dataset that produces no examples.

Recovery:

- Confirm `train_data_dir` contains training mmCIFs.
- Confirm `train_alignment_dir` matches the intended layout: per-chain alignment directories, or alignment DB shard files when `--alignment_index_path` is used.
- Confirm `--alignment_index_path` points to the index for the DB shards and that shard paths are valid from the training host.
- Confirm `--train_chain_data_cache_path` and `--template_release_dates_cache_path` point to JSON files generated for the same structure/template set.
- Confirm `--obsolete_pdbs_file_path` exists for PDB/OpenProteinSet-style training.
- Route cache/index regeneration and structural validation to `../data-preparation/`.

## Distributed Seed Error

Symptom: OpenFold raises `For distributed training, --seed must be specified`.

Recovery: add a stable integer `--seed` whenever `--gpus > 1` or `--num_nodes > 1`. Keep the same seed when resuming a distributed run unless there is a deliberate experiment change.

## DeepSpeed and Precision Conflict

Symptom: OpenFold raises `DeepSpeed and FP16 training are not compatible`.

Recovery:

- Do not combine `--precision 16` with `--deepspeed_config_path`.
- Prefer BF16 on A100-class GPUs when supported.
- Ensure the DeepSpeed JSON enables only one of `bfloat16`, `fp16`, or `amp`.
- If the hardware cannot run BF16, choose a non-DeepSpeed path or get cluster-specific guidance before using FP16/AMP.

## GPU or Runtime Is Impossible

Symptoms: CUDA unavailable, no GPUs allocated, CPU-only host, out-of-memory at startup, missing NCCL/MPI, or optional acceleration imports fail.

Recovery:

- Do not attempt full OpenFold training on CPU-only hardware.
- Reduce crop size or MSA sizes with `--experiment_config_json` only after confirming scientific intent.
- Use `--accumulate_grad_batches` to alter effective batch size, not memory per forward pass.
- Repair CUDA/PyTorch/DeepSpeed/MPI in `../installation-assets/` before retrying.
- For missing acceleration kernels, decide whether the target command can run without that feature or whether the extension must be rebuilt.

## W&B, DLLogger, or Logger Problems

Symptoms: W&B authentication prompts, unavailable DLLogger-style logging dependencies in an older/local fork, permission errors in `output_dir`, duplicate run IDs, missing package freeze artifact, or rank-specific logging issues.

Recovery:

- Omit `--wandb` for a local smoke/dry run.
- If W&B is required, set `--experiment_name`, `--wandb_project`, and optionally `--wandb_entity`/`--wandb_id` deliberately.
- If a target checkout or fork uses DLLogger, install/enable it in the runtime environment or disable that logger before treating training itself as broken.
- Ensure `output_dir` is writable and shared where needed.
- In MPI runs, confirm rank environment variables are set consistently before assuming rank-zero logging behavior is correct.

## Checkpoint Mismatch

Symptoms: missing `latest` in a DeepSpeed checkpoint directory, missing `global_step`, state-dict key mismatches, optimizer resume failure, or incompatible JAX/OpenFold weights.

Recovery:

- For exact resume, use `--resume_from_ckpt` without `--resume_model_weights_only true` and match the original strategy where possible.
- For fine-tuning, use `--resume_from_ckpt` plus `--resume_model_weights_only true` and usually `--config_preset finetuning`.
- For JAX `.npz` parameters, use `--resume_from_jax_params` and do not pass `--resume_from_ckpt`.
- Route low-level checkpoint conversion or key-shape diagnosis to `../model-apis/`.
