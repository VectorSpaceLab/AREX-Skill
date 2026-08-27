# Training and merge workflows

## Data layout

The supervised instruction builder expects JSON records with these keys:

- `instruction`
- `input` (optional, may be empty)
- `output`

Multiple JSON files may be passed in and are concatenated after tokenization.

## Main command families

### Pretraining
- `run_pt.sh` demonstrates the expected DeepSpeed and LoRA arguments for the pretraining path.
- `run_clm_pt_with_peft.py` is the main CLI for causal language-model pretraining with PEFT.

### Supervised fine-tuning
- `run_sft.sh` demonstrates the expected DeepSpeed and LoRA arguments for the SFT path.
- `run_clm_sft_with_peft.py` is the main CLI for instruction tuning.
- `build_dataset.py` tokenizes instruction data, stores a cached processed dataset, and supplies the collator.

### Merge/export
- `merge_llama2_with_chinese_lora_low_mem.py` merges a base HF checkpoint with one LoRA adapter.
- It can export either a Hugging Face directory or PTH shards.

## Common argument patterns

| Flag | Meaning |
| --- | --- |
| `--model_name_or_path` | Base model checkpoint used for initialization |
| `--tokenizer_name_or_path` | Tokenizer path used for training or merge |
| `--dataset_dir` | Root directory or JSON dataset path |
| `--validation_file` | Explicit validation split for SFT |
| `--output_dir` | Target directory for checkpoints or merged weights |
| `--deepspeed` | DeepSpeed configuration file |
| `--lora_rank`, `--lora_alpha`, `--lora_dropout` | PEFT LoRA configuration |
| `--modules_to_save` | Extra modules kept in the adapter checkpoint |
| `--load_in_kbits` | Quantized training/finetuning mode |
| `--use_flash_attention_2` | Optional attention acceleration |

## Output conventions

- Pretraining saves PEFT checkpoints under `pt_lora_model/`.
- SFT saves PEFT checkpoints under `sft_lora_model/`.
- Merge/export writes a full model directory or PTH shard set, depending on the selected output type.

## Notes on the vendored PEFT copy

The repository bundles a local `peft/` implementation under `scripts/training/peft/`. Run the training scripts from this directory tree so that the vendored package stays on the import path and the training CLIs behave as expected.
