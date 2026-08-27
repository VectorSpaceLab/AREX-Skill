# RWKV-LM cross-cutting troubleshooting

## Install/import checks

The repository is not a normal installable Python package with `pyproject.toml`.
Most workflows are script- and checkout-based. Use a Python environment with
PyTorch, NumPy, `pytorch-lightning==1.9.5`, DeepSpeed, `rwkv`, and optional HF
packages for export/evaluation tasks.

Run the bundled check:

```bash
python scripts/check_runtime.py --check-cuda
```

A successful PyTorch CUDA tensor allocation proves the wheel can see the GPU. It
does not prove source CUDA extensions from `cuda/` can compile.

## Backend mismatch

Common RWKV-LM GPU failures are caused by:

- torch CUDA wheel incompatible with driver or GPU compute capability
- missing CUDA toolkit or `nvcc`
- missing `CUDA_HOME`
- old torch extension cache after an interrupted compile
- mixing kernels from v5, v7 `train_temp`, and v8 toy directories

If the task only needs data preparation, prompt rendering, or architecture
reasoning, do not require GPU custom-kernel verification. If the task claims
fast CUDA inference or full training, verify the actual backend.

## Checkpoint and tokenizer mismatch

RWKV scripts often hard-code local checkpoint paths and model dimensions. Replace
those with user-provided values and verify:

- checkpoint file exists and loads on CPU
- `n_layer`, `n_embd`, head size, and `vocab_size` match the script
- tokenizer family matches the checkpoint
- older Pile/v4 tokenizers are not confused with `rwkv_vocab_v20230424`

## Data/config mismatch

Training errors often come from `ctx_len`, `magic_prime`, `my_exit_tokens`, and
data prefix inconsistencies rather than model code. Use `training-data` helpers
before launching training.

## External data and network

MiniPile, Pile, MMLU, checkpoints, and Hugging Face models may require downloads.
Do not start network access, large downloads, or long benchmark/training runs
unless the user explicitly wants that operation.

## Which sub-skill to read next

- Data conversion or training command: `training-data`.
- Prompt sampling or MMLU: `inference-evaluation`.
- Tensor names, state shape, Qwen export: `architecture-reference`.
- RWKV-8/ROSA toy research scripts: `rosa-experiments`.
