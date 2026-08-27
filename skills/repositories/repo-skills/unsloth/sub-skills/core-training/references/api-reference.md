# Unsloth Core API Reference

This reference covers the public code-first training surface that future agents need for safe planning. It distills source, tests, and installed package signatures; it does not require reopening the source repository.

## Import And Backend Surface

Import order matters because Unsloth patches `trl`, `transformers`, and `peft` at import time.

```python
import unsloth
from unsloth import FastLanguageModel, is_bfloat16_supported
```

- `unsloth.DEVICE_TYPE` reports the active backend such as `cuda` or `mlx` when import succeeds.
- `is_bfloat16_supported()` and alias `is_bf16_supported()` are the dtype probes to use before trainer argument construction.
- GPU import requires compatible `torch`, `numpy`, `unsloth_zoo`, `triton`, and usually `bitsandbytes` for 4-bit QLoRA.
- Apple Silicon + MLX can expose lightweight `FastLanguageModel`, `FastModel`, `FastVisionModel`, `RawTextDataLoader`, and `TextPreprocessor`; `FastSentenceTransformer` and `UnslothVisionDataCollator` are not supported there.
- `UNSLOTH_FORCE_GPU_PATH=1` forces the GPU path on systems that might otherwise detect MLX.
- CPU/no-torch installations are useful for Studio chat/data-recipe or lightweight config work, not for Core GPU training.

## Model Loader Classes

| Class | Use When | Notes |
| --- | --- | --- |
| `FastLanguageModel` | Text causal LM finetuning and common notebook-style QLoRA | The high-frequency text entry point; returns `(model, tokenizer)` from `from_pretrained`. |
| `FastModel` | Modern unified text, vision/audio-capable, task-model, Whisper/TTS, or custom `auto_model` flows | Accepts extra multimodal/task kwargs and can choose sequence-classification auto classes from config. |
| `FastVisionModel` | Vision-language training and inference | Subclass of `FastModel`; pair with vision-specific LoRA flags and usually `UnslothVisionDataCollator`. |
| `FastTextModel` | Text-only alias of `FastModel` | Use when the unified loader is preferred but the task is explicitly text-only. |
| `FastSentenceTransformer` | Embedding/sentence-transformer finetuning | Uses sentence-transformers conventions, pooling modes, and feature-extraction PEFT defaults. |

### `FastLanguageModel.from_pretrained`

Installed signature highlights:

```python
FastLanguageModel.from_pretrained(
    model_name="unsloth/Llama-3.2-1B-Instruct",
    max_seq_length=2048,
    dtype=None,
    load_in_4bit=True,
    load_in_8bit=False,
    load_in_16bit=False,
    full_finetuning=False,
    token=None,
    device_map="sequential",
    trust_remote_code=False,
    use_gradient_checkpointing="unsloth",
    fast_inference=False,
    max_lora_rank=64,
    text_only=False,
    **kwargs,
)
```

Planning rules:

- Use one quantization mode at a time: 4-bit, 8-bit, 16-bit, or FP8; the loader rejects combinations.
- `load_in_4bit=True` is the default QLoRA path and requires a backend where bitsandbytes-style loading is available.
- `full_finetuning=True` disables LoRA/QLoRA quantization flags internally; plan more VRAM and do not rely on `get_peft_model` to add adapters.
- `dtype=None` chooses `bfloat16` on supported devices, otherwise `float16`; override with `torch.float32` only for deliberate full/mixed precision needs.
- `trust_remote_code=False` is safer; set it true only when the model repository requires custom code and the user accepts that risk.
- `token` is for private or gated model access; do not hard-code secrets in configs or generated scripts.
- `fast_inference=True` uses a vLLM-oriented path and can conflict with some training/LoRA combinations.
- `text_only=True` is opt-in for vision-capable configs that have a valid text decoder; use `FastVisionModel` for multimodal inputs.

### `FastModel.from_pretrained` And `FastVisionModel.from_pretrained`

`FastModel.from_pretrained` and `FastVisionModel.from_pretrained` include the same core loader flags plus multimodal/task parameters:

- `return_logits`, `fullgraph`, `auto_model`, `whisper_language`, `whisper_task`, `unsloth_force_compile`, `target_parameters`, and `text_only`.
- Passing `config=` can preserve sequence-classification labels such as `num_labels`, `id2label`, `label2id`, and `problem_type`.
- For vision/audio-capable models, `text_only=True` skips vision/audio towers only when the family has a compatible text decoder; otherwise the loader falls back to the full model.

## LoRA And PEFT Setup

### Text LoRA

Installed `FastLanguageModel.get_peft_model` highlights:

```python
FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0.0,
    bias="none",
    finetune_last_n_layers=None,
    use_gradient_checkpointing="unsloth",
    random_state=3407,
    max_seq_length=2048,
    use_rslora=False,
    modules_to_save=None,
    init_lora_weights=True,
    qat_scheme=None,
    target_parameters=None,
    ensure_weight_tying=False,
    **kwargs,
)
```

- Default target modules cover attention projections and MLP projections for decoder LMs.
- Keep `lora_dropout=0.0` and `bias="none"` for the fastest patched path unless the task needs a different PEFT recipe.
- Use `modules_to_save=["embed_tokens", "lm_head"]` when new tokens or vocab changes require training embeddings/output heads; Unsloth may auto-add these if it detects new tokens.
- `finetune_last_n_layers=N` converts to a final-layer slice when the total transformer layer count is discoverable.
- MoE models can use regex-like `target_modules` patterns that let Unsloth discover expert `target_parameters`; explicit dotted single-module targets do not trigger MoE parameter discovery.
- `use_rslora=True` and `init_lora_weights="loftq"` depend on PEFT support; LoftQ cannot be used with an already quantized `load_in_4bit=True` model.
- In full finetuning mode, `get_peft_model` intentionally has no adapter effect.

### Vision LoRA

`FastVisionModel.get_peft_model` accepts the text LoRA knobs and adds filter switches:

```python
FastVisionModel.get_peft_model(
    model,
    target_modules=None,
    finetune_vision_layers=True,
    finetune_language_layers=True,
    finetune_attention_modules=True,
    finetune_mlp_modules=True,
    finetune_last_n_layers=None,
    **kwargs,
)
```

- `target_modules=None` or `"all-linear"` lets Unsloth build a regex from the vision/language and attention/MLP filters.
- If explicit target modules are provided while filters are false, Unsloth constrains the explicit modules by those filters.
- `fast_inference=True` can reject vision-layer LoRA or unsupported VLM LoRA combinations; switch to text-layer LoRA or disable fast inference.

### Sentence Transformer LoRA

`FastSentenceTransformer.from_pretrained` defaults to `load_in_16bit=True` and `load_in_4bit=False`, with `pooling_mode="mean"` and `for_inference=False`.

`FastSentenceTransformer.get_peft_model` defaults to encoder-style targets:

```python
target_modules=["query", "key", "value", "dense"]
```

- The default task type is `FEATURE_EXTRACTION`.
- Gradient checkpointing defaults to `False` because it can conflict with `torch.compile` on fast encoder paths.
- For quantized encoders, Unsloth prepares k-bit training and falls back gracefully if a model cannot enable gradient checkpointing.

## Trainer Surface

`UnslothTrainingArguments` extends TRL `SFTConfig` when available, otherwise Transformers `TrainingArguments`.

Additional fields:

- `embedding_learning_rate`: separates LR for embedding/output-head modules saved by PEFT.
- `q_galore_config`: enables Q-GaLore optimizer integration through `QGaloreConfig`.

`UnslothTrainer` subclasses `trl.SFTTrainer` and customizes optimizer creation for embedding LR and Q-GaLore. Standard TRL `SFTTrainer` can also be used after importing Unsloth; Unsloth patches backward-compatible parameter handling and auto packing/padding-free behavior.

Packing utilities from `unsloth.utils`:

- `configure_sample_packing(config)` sets `packing=True`, `padding_free=True`, and `remove_unused_columns=False`.
- `configure_padding_free(config)` sets padding-free batching without sample packing.
- Unsloth auto-skips packing for custom data collators, processor-based or vision-language models, selected blocklisted model families, or forced logits.

## Chat And Data Utility APIs

Installed `get_chat_template` signature:

```python
get_chat_template(
    tokenizer,
    chat_template="chatml",
    mapping={"role": "role", "content": "content", "user": "user", "assistant": "assistant"},
    map_eos_token=True,
    system_message=None,
    patch_saving=True,
    use_zoo_tokenizer_patch=False,
)
```

- Pass a tokenizer returned by a `Fast*` loader.
- Use `mapping` when dataset rows use custom role/content/user/assistant field names or aliases.
- Common template names include `chatml`, `unsloth`, `alpaca`, `llama`, `llama-3`, `gemma`, `gemma_chatml`, `gemma4`, `mistral`, `phi-3`, `vicuna`, and related aliases.
- Some templates map stop tokens or EOS tokens; leave `map_eos_token=True` unless you intentionally manage EOS yourself.

Installed `standardize_sharegpt` signature:

```python
standardize_sharegpt(
    dataset,
    tokenizer=None,
    aliases_for_system=["system"],
    aliases_for_user=["user", "human", "input"],
    aliases_for_assistant=["gpt", "assistant", "output"],
    batch_size=1000,
    num_proc=None,
)
```

- Use it for ShareGPT-style conversation datasets before applying a chat template or formatting function.
- Ensure every message can map to a system/user/assistant role and has text content.
- `train_on_responses_only` is also exported from `unsloth.chat_templates` for masking prompt tokens in SFT recipes.

## Raw Text Helpers

`RawTextDataLoader(tokenizer, chunk_size=2048, stride=512, return_tokenized=True)` supports `.txt`, `.md`, `.json`, `.jsonl`, and `.csv` text extraction.

- `chunk_size` must be positive.
- `stride` must be smaller than `chunk_size`.
- Tokenized chunks contain `input_ids`, `attention_mask`, and `labels` equal to `input_ids` for causal LM.
- Text chunks contain a `text` column.

`TextPreprocessor` provides `clean_text`, `extract_sections`, `add_structure_tokens`, and `validate_dataset`. `clean_text` normalizes line endings, collapses whitespace, strips non-ASCII characters, preserves paragraph breaks, and is intended for raw text pretraining data preparation.
