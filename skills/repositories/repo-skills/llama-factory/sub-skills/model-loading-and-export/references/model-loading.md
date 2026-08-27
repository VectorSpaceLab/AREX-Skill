# Model Loading

## v0 Loading Path

LlamaFactory defaults to the v0 architecture. `llamafactory-cli` and `lmf` dispatch through the CLI entry point, and `USE_V1=1` switches to the experimental v1 tree. For this sub-skill, assume v0 unless the user explicitly sets `USE_V1=1`.

The v0 loader sequence is:

1. Parse config into `ModelArguments`, `DataArguments`, `FinetuningArguments`, and runtime arguments.
2. Build Hugging Face init kwargs from `model_name_or_path`, `trust_remote_code`, `cache_dir`, `model_revision`, and `hf_hub_token`.
3. Try hub redirection/mirror resolution before model/tokenizer loading.
4. Load tokenizer with `AutoTokenizer.from_pretrained`, falling back between fast and slow tokenizers on `ValueError`.
5. Patch tokenizer, then try `AutoProcessor.from_pretrained`; processor failures are logged and ignored unless the downstream task requires processor features.
6. Load config with `AutoConfig.from_pretrained`, patch config, choose a model auto-class, load or initialize weights, patch the model, register autoclass metadata, initialize/merge adapters, optionally wrap a value head, then switch train/eval mode.

## Core Model Arguments

Common loader fields:

- `model_name_or_path`: local model directory or hub id; required.
- `adapter_name_or_path`: one or more comma-separated adapter paths/ids; normalized to a list.
- `adapter_folder`: subfolder that contains adapter weights.
- `cache_dir`: cache location for model/tokenizer/config artifacts.
- `model_revision`: branch, tag, or commit; defaults to `main`.
- `trust_remote_code`: required for many Qwen, multimodal, or custom architectures; only enable when the source is trusted.
- `hf_hub_token`, `ms_hub_token`, `om_hub_token`: hub credentials; keep them out of checked-in configs.
- `use_fast_tokenizer`: default true; loader automatically retries the opposite tokenizer implementation after a tokenizer `ValueError`.
- `split_special_tokens`, `add_tokens`, `add_special_tokens`, `new_special_tokens_config`, and `init_special_tokens`: control tokenizer growth and embedding initialization.
- `resize_vocab`: resizes embedding layers after tokenizer/template changes; risky or unsupported for quantized models.

Hub mirror behavior is selected by environment variables, not by changing `model_name_or_path` syntax:

- `USE_MODELSCOPE_HUB=1` routes supported model downloads through ModelScope.
- `USE_OPENMIND_HUB=1` routes supported model downloads through Modelers/OpenMind.
- Keep mirror credentials in environment variables or secret stores, not in runtime skill examples.

## Tokenizer and Processor Behavior

Tokenizer loading is fatal if both fast and slow attempts fail. Processor loading is best-effort: failures are logged and the loader returns `processor: None`. For multimodal models, a missing processor usually means generation/training will fail later when images, video, or audio are processed.

When diagnosing tokenizer/processor failures, collect:

- Exact `model_name_or_path`, `model_revision`, and whether it is local or hub-hosted.
- Whether `trust_remote_code: true` is required by the model card.
- Whether the model id is gated/private and whether a token is available.
- Whether the cache contains a partial/corrupt snapshot.
- Whether the tokenizer requires slow tokenizers, SentencePiece, tiktoken, protobuf, or model-specific processor dependencies.

## Model Auto-Class Selection

After config loading and patching, the loader chooses an auto-class by model mapping:

- Image-text configs: `AutoModelForImageTextToText`.
- Seq2Seq/audio-text configs: `AutoModelForSeq2SeqLM`.
- Qwen-Omni text-to-waveform configs: `AutoModelForTextToWaveform`, then may select the `thinker` submodule.
- Otherwise: `AutoModelForCausalLM`.

`train_from_scratch: true` calls `from_config` instead of `from_pretrained`; otherwise weights are loaded from the model path/hub id.

## Patches and Loader Features

The model patch layer can configure or alter:

- Attention implementation (`flash_attn`), RoPE scaling, KV cache, LongLoRA shift attention, MoE auxiliary loss, visual tower/projector dtype, and special multimodal model behavior.
- Quantization setup before weight loading.
- Gradient checkpointing and trainability preparation.
- Embedding resize and new-token initialization.
- Unsloth, Liger Kernel, MoD conversion/load, KTransformers, and temporary v1 kernel application when enabled.
- Model-specific compatibility patches such as Qwen Omni, Qwen3.5, Llava/ChatGLM/InternLM value-head save handling, and architecture quirks.

Keep patch recommendations narrow. Do not suggest enabling a kernel/backend unless the user has the package and hardware it requires.

## Adapter Loading and Merging

Adapter handling happens after the base model is loaded and patched.

Important rules:

- `adapter_name_or_path` accepts comma-separated adapters. Earlier adapters can be merged into the base before the final adapter is loaded/resumed.
- Quantized models, DeepSpeed ZeRO-3, KTransformers, and Unsloth restrict adapter handling to a single adapter in important paths and often disable mergeability.
- If training and `create_new_adapter: false`, the last adapter is treated as the adapter to resume; earlier adapters are merged if mergeable.
- If training and `create_new_adapter: true`, supplied adapters are treated as merge inputs and a fresh adapter is created.
- `lora_target: all` resolves to all supported linear modules, with multimodal forbidden modules filtered out.
- DoRA is rejected for PTQ-quantized models except bitsandbytes-style quantization.
- When `resize_vocab: true` and LoRA is used without `additional_target`, embedding modules may be added as trainable/saved targets so new-token weights are preserved.

## Fine-Tuning Types In Loader Scope

This sub-skill covers model-side setup, not the training run itself:

- `finetuning_type: full`: all non-forbidden parameters are trainable; trainable parameters may be cast to fp32.
- `finetuning_type: freeze`: hidden-layer subsets and optional extra modules are made trainable; `use_llama_pro` requires layer divisibility.
- `finetuning_type: lora`: creates, resumes, or merges PEFT LoRA adapters.
- `finetuning_type: oft`: creates OFT adapters with `oft_rank`, `oft_block_size`, and target modules.

Route optimizer choice, batch sizes, stages, distributed launch, and metrics to `training-and-configs`.

## Value Head and Reward Models

When `add_valuehead` is requested, LlamaFactory wraps the base model with TRL's value-head model and tries to load value-head weights from the final adapter or base model path. Recognized value-head files are the safe-tensor and PyTorch value-head names used by LlamaFactory.

For RM export (`stage: rm`), export copies value-head weights from the final adapter path or model path into the export directory when they exist. If value-head weights are missing, LlamaFactory logs an informational message and continues; only treat it as fatal when the user's task explicitly requires an RM/value-head artifact.

## Minimal Load-Focused Config Pattern

```yaml
model_name_or_path: Qwen/Qwen3-4B-Instruct-2507
template: qwen3_nothink
trust_remote_code: true
model_revision: main
cache_dir: ./cache
```

For private or gated models, use an environment-provided token rather than committing `hf_hub_token`.
