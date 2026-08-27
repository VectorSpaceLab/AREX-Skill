# Checkpoint Utilities

LlamaFactory includes utility scripts for checkpoint conversion and adapter/model initialization. Treat these utilities as reference-only plans in agent guidance unless the user explicitly authorizes the run. They can load full models, rewrite large checkpoint trees, allocate GPU/CPU memory, and overwrite output directories.

## PiSSA Initialization

PiSSA initialization creates an initialized LoRA adapter and a base model output directory.

Conceptual flow:

1. Load tokenizer and causal LM from `model_name_or_path` with trusted remote code.
2. Create a PEFT LoRA config with `init_lora_weights` set to PiSSA or PiSSA iterative FSVD.
3. Save an initialized adapter under the output directory.
4. Unload and save the base model plus tokenizer.
5. Fine-tune with the saved base model, the initialized adapter, `finetuning_type: lora`, `pissa_init: false`, and `pissa_convert: true`.

Planning fields:

- `pissa_iter: -1` disables iterative FSVD and uses plain PiSSA; positive values choose the iteration count.
- `lora_rank`, `lora_alpha`, `lora_dropout`, and `lora_target` must match the intended training config.
- Optional `quantization_bit: 4` can be used later for QLoRA-style fine-tuning, not during the destructive initialization itself unless the user plans it carefully.

## LoftQ Initialization

LoftQ initialization creates a quantization-aware LoRA adapter and base model output.

Planning fields:

- `loftq_bits`: usually `4`.
- `loftq_iter`: number of LoftQ iterations.
- `lora_rank`, `lora_alpha`, `lora_dropout`, and `lora_target`: same as the later training config.

Fine-tune the result by using the generated base output as `model_name_or_path`, generated adapter as `adapter_name_or_path`, `finetuning_type: lora`, and `quantization_bit` matching the LoftQ bits.

## LLaMA-Pro Block Expansion

The LLaMA-Pro utility performs block expansion for compatible decoder-only families such as LLaMA, Mistral, Qwen2, or Yi-style models.

Important constraints:

- `num_hidden_layers` must be divisible by `num_expand`.
- The utility writes a modified config, tokenizer files, and newly sharded model weights.
- New expanded layers clone or zero selected matrices from existing layers.
- The resulting model is intended for freeze tuning with `use_llama_pro: true` and `freeze_trainable_layers` equal to the expansion count.
- Safe-tensor saving may remove tied `lm_head` before writing because shared tensors are not accepted by safetensors in this path.

Treat this as a large checkpoint rewrite. Ask for explicit source, output, disk, and compute confirmation before running.

## DCP and Hugging Face Conversion

LlamaFactory has utilities for converting between Hugging Face model directories and PyTorch Distributed Checkpoint (DCP) directories.

HF to DCP planning:

- Inputs: `hf_path` and `dcp_path`.
- Loads config, resolves architecture class when present, loads model on CPU in bfloat16, and saves state dict with DCP.

DCP to HF planning:

- Inputs: `dcp_path`, `hf_path`, and `config_path`.
- Loads config, initializes model on CPU in bfloat16, loads DCP state dict, saves HF model/config.
- Tokenizer files are not automatically restored; copy or regenerate tokenizer artifacts from the original model source after conversion.

Both directions can be slow and disk-heavy. Do not treat them as lightweight validation.

## Megatron and Other Merge Utilities

Checkpoint merge utilities can be backend-specific and destructive. Before using any merge utility, require:

- Source checkpoint format and exact directory layout.
- Target format and output directory.
- Tensor/pipeline/expert parallel assumptions.
- Whether tokenizer/config files are included or need to be copied separately.
- Confirmation that the output directory may be created or overwritten.

## Safe Agent Workflow

1. First propose a dry plan with input paths, output paths, expected format, dependencies, and risk.
2. Verify free disk and read/write permissions before a real run.
3. Prefer CPU/offline conversion only when the script supports it; otherwise call out GPU/backend requirements.
4. Never run conversion against the only copy of a checkpoint without a backup.
5. After conversion, verify `config.json`, tokenizer files, model weight index or shard files, and any adapter/value-head files needed by the target flow.
