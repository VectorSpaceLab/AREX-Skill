# Troubleshooting

Use this matrix when a data or training script fails before or during the first batch. The goal is to diagnose the loader / parser / runtime category before changing model code.

## Common failure modes

| Symptom | Likely cause | Where it usually appears | Suggested fix |
|---|---|---|---|
| `json.decoder.JSONDecodeError`, `KeyError`, or empty examples | Wrong JSON / JSONL field names, or a file that is not actually JSONL | classification, LCSTS, T5 task data, pretraining corpora | Match the loader schema exactly: `text`, `summary`, `question`, `choice`, `texta`, `textb`, `answer`, `label`, `id`, or the sequence-tagging file layout. |
| Missing labels or broken spans | `labels.txt` is missing, the label inventory does not match `decode_type`, or the corpus uses a different tag scheme | sequence tagging | Rebuild `labels.txt` and choose the collator that matches the decode type. Normalize `M-` to `I-` before `get_entities` if the loader expects it. |
| `Unknown sampler type` | `sampler_type` is not `single` or `random` | `UniversalDataModule` pretraining paths | Use one of the supported values. If you need a custom order, do not invent a new sampler name. |
| Repeated batches after resume | `replace_sampler_ddp` overrode a custom sampler, or checkpoint resume did not preserve consumed samples | pretraining / distributed runs | Keep `replace_sampler_ddp=False` when a custom sampler is in use, and keep the checkpoint path aligned with the consumed-sample state. |
| `max_epoch` or `sheduler_type` does nothing | Lightning / shell flag typo | copied shell scripts | Use `max_epochs` and `scheduler_type`. Verify the flag name with [scripts/inspect_training_args.py](../scripts/inspect_training_args.py). |
| `torchmetrics.Accuracy()` import or constructor error | Torchmetrics API mismatch | classification and some validation helpers | The verified environment uses `torchmetrics==0.11.4`. Pin a compatible version or update the call site to the newer task-specific API. |
| `ImportError: DeepSpeedCPUAdam` / `FusedAdam` | DeepSpeed is missing or its import path is broken | optimizer setup | Install an importable `deepspeed` first. If you only need CPU-safe inspection, do not claim DeepSpeed training is verified. |
| `fused kernels configured but not installed` | Megatron fused CUDA extensions were not compiled | `megatron_deepspeed` or fused-kernel tests | Treat fused kernels as optional. Compile them only if you need the Megatron path and have a matching CUDA toolchain. |
| CUDA extension build failure | Missing `nvcc`, incompatible CUDA/PyTorch combo, or no build toolchain | fused kernel install or optional Megatron path | Verify `CUDA_HOME`, the toolkit version, and the torch/CUDA pairing. Skip the optional path if you only need the data-train skill. |
| `ModuleNotFoundError: fengshen.data.fs_datasets` | The `fs_datasets` submodule is not initialized | `datasets_name` and cached dataset loaders | Initialize the submodule or use a local JSON / HF dataset path that the loader already supports. |
| `ModuleNotFoundError: fengshen.data.mmap_index_dataset` | Legacy absolute import path inside the mmap data module | mmap dataset inspection or loading | Use the bundled inspector script, which patches the alias, or normalize the import path in your environment. |
| `load_ckpt_path` is ignored | The checkpoint directory does not exist | checkpointed pretraining | Create the path first or remove the missing resume path before launching. The checkpoint wrapper nulls missing paths to avoid a hard crash. |
| Validation looks fine but F1 is zero | The label markup and decode type do not match | sequence tagging | Check that `linear/crf` use full tags and `span/biaffine` use entity types, then rerun the tiny label checker. |

## JSON / JSONL schema reminders

- Some loaders use `json.loads` and require strict JSONL.
- Some legacy QA loaders use `eval` on trusted dict-like lines; do not feed them untrusted files.
- Some loaders silently fall back to empty strings or zero labels when a field is missing. That is convenient for demos and dangerous for real training.

## Data-loader specific notes

### Classification

- If the local JSON keys do not match `texta_name`, `textb_name`, `label_name`, or `id_name`, the loader may read the wrong fields.
- If you use `dataset_name`, the expected splits are `train`, `validation`, and `test`.

### Sequence tagging

- `labels.txt` must match the chosen `decode_type`.
- `span` and `biaffine` do not use the same label inventory as `linear` and `crf`.
- `get_entities` only supports `bio`, `bios`, and `bioes` markup.

### T5 / QA / dialog

- `train_split_size` changes whether the loader creates its own split.
- `tokenizer_type` changes whether MT5 or BERT tokenization is used.
- `max_seq_length`, `max_enc_length`, `max_dec_length`, and `max_target_length` must be consistent with the collator and the labels you expect to decode.

### Pretraining / Megatron

- Keep the data-prep and runtime commands separate.
- Keep the sampler and checkpoint-resume path aligned.
- Keep the optional fused-kernel build separate from the normal CPU-safe inspection path.

## Quick recovery flow

1. Validate one tiny record with the bundled checker scripts.
2. Print the parser groups with [scripts/inspect_training_args.py](../scripts/inspect_training_args.py).
3. Confirm the data file format against [data-formats.md](data-formats.md).
4. Confirm the runtime flags against [training-arguments.md](training-arguments.md).
5. Only then start a large or distributed run.
