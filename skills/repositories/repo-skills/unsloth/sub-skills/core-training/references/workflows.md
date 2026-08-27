# Code-First Core Training Workflows

These workflows are safe planning templates. They show the sequence and key options to generate for users, but they should not be executed during skill validation because model loading can download weights and require GPU/MLX resources.

## Preflight Before Any Recipe

1. Run `scripts/inspect_unsloth_core.py` in the target environment to confirm imports, backend, key signatures, and optional dependency availability.
2. Decide whether the user wants Core Python APIs, CLI orchestration, export, or Studio. Route CLI/export/Studio to sibling sub-skills before drafting code.
3. Confirm the target model family, dataset shape, context length, memory budget, and whether private/gated model access is needed.
4. Validate a tiny YAML/JSON config and optional dataset sample with `scripts/validate_training_config.py`.
5. Generate training code with `import unsloth` before `transformers`, `trl`, or `peft` imports.

## Text QLoRA SFT Recipe

Use this for the common local JSONL chat or text SFT request with constrained VRAM.

```python
import unsloth
from unsloth import FastLanguageModel, is_bfloat16_supported
from unsloth.chat_templates import get_chat_template, standardize_sharegpt, train_on_responses_only
from datasets import load_dataset
from trl import SFTConfig, SFTTrainer

max_seq_length = 2048
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Llama-3.2-1B-Instruct",
    max_seq_length=max_seq_length,
    dtype=None,
    load_in_4bit=True,
    token=None,
)

tokenizer = get_chat_template(
    tokenizer,
    chat_template="chatml",
    mapping={"role": "role", "content": "content", "user": "user", "assistant": "assistant"},
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0.0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)

dataset = load_dataset("json", data_files="train.jsonl", split="train")
dataset = standardize_sharegpt(dataset, tokenizer=tokenizer)

def formatting_prompts_func(examples):
    convos = examples["conversations"]
    texts = [tokenizer.apply_chat_template(c, tokenize=False, add_generation_prompt=False) for c in convos]
    return {"text": texts}

dataset = dataset.map(formatting_prompts_func, batched=True)

args = SFTConfig(
    output_dir="outputs",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    max_steps=60,
    learning_rate=2e-4,
    logging_steps=1,
    optim="adamw_8bit",
    weight_decay=0.01,
    lr_scheduler_type="linear",
    seed=3407,
    bf16=is_bfloat16_supported(),
    fp16=not is_bfloat16_supported(),
    report_to="none",
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    args=args,
)
trainer = train_on_responses_only(trainer)
# trainer.train()
```

Planning notes:

- Keep the `trainer.train()` line commented in generated plans unless the user explicitly asks to run training in a prepared environment.
- If the dataset is already a single text field, skip `standardize_sharegpt` and use `dataset_text_field="text"`.
- If new tokens are added, include `modules_to_save=["embed_tokens", "lm_head"]` or explain that Unsloth can auto-enable them when detected.

## Full Finetuning Recipe

Use this only when the user has enough memory and asks for non-adapter training.

```python
import unsloth
from unsloth import FastLanguageModel, is_bfloat16_supported
from trl import SFTConfig, SFTTrainer

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Llama-3.2-1B-Instruct",
    max_seq_length=2048,
    dtype=None,
    load_in_4bit=False,
    load_in_8bit=False,
    load_in_16bit=False,
    full_finetuning=True,
)

args = SFTConfig(
    output_dir="outputs-full",
    learning_rate=2e-5,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    bf16=is_bfloat16_supported(),
    fp16=not is_bfloat16_supported(),
    report_to="none",
)

trainer = SFTTrainer(model=model, tokenizer=tokenizer, train_dataset=dataset, dataset_text_field="text", args=args)
# trainer.train()
```

Planning notes:

- Do not call `get_peft_model` expecting adapters when `full_finetuning=True`; Unsloth treats it as a no-op.
- Avoid combining full finetuning with `load_in_4bit`, `load_in_8bit`, or `load_in_fp8`; the loader disables LoRA/quantization flags or raises for incompatible combinations.
- Use lower learning rates than LoRA recipes and plan more checkpoint/storage/VRAM capacity.

## Vision Or Multimodal LoRA Recipe

Use `FastVisionModel` or `FastModel` for VLMs. Route Studio UI training requests to `../studio-runtime/SKILL.md`.

```python
import unsloth
from unsloth import FastVisionModel, UnslothVisionDataCollator, is_bfloat16_supported
from trl import SFTConfig, SFTTrainer

model, processor = FastVisionModel.from_pretrained(
    model_name="unsloth/Llama-3.2-11B-Vision-Instruct-bnb-4bit",
    max_seq_length=2048,
    load_in_4bit=True,
)

model = FastVisionModel.get_peft_model(
    model,
    r=16,
    finetune_vision_layers=False,
    finetune_language_layers=True,
    finetune_attention_modules=True,
    finetune_mlp_modules=True,
    lora_alpha=16,
    lora_dropout=0.0,
    bias="none",
)

args = SFTConfig(
    output_dir="outputs-vlm",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    bf16=is_bfloat16_supported(),
    fp16=not is_bfloat16_supported(),
    report_to="none",
)

trainer = SFTTrainer(
    model=model,
    processing_class=processor,
    train_dataset=dataset,
    data_collator=UnslothVisionDataCollator(model, processor),
    args=args,
)
# trainer.train()
```

Planning notes:

- Keep vision-layer LoRA disabled when the user wants text-only adaptation or when `fast_inference=True` is involved.
- Use `finetune_last_n_layers=N` for a late-layer adapter budget when the model exposes layer counts.
- Ensure local image/video paths exist before training; the Unsloth vision collator raises for missing videos after applying a formatting function.

## Sentence Transformer Recipe

Use this for embedding-model finetuning, not for causal chat SFT.

```python
import unsloth
from unsloth import FastSentenceTransformer

model = FastSentenceTransformer.from_pretrained(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    max_seq_length=512,
    load_in_4bit=False,
    load_in_16bit=True,
    pooling_mode="mean",
)

model = FastSentenceTransformer.get_peft_model(
    model,
    r=16,
    target_modules=["query", "key", "value", "dense"],
    lora_alpha=16,
    lora_dropout=0.0,
    use_gradient_checkpointing=False,
)
```

Planning notes:

- Default PEFT task type is `FEATURE_EXTRACTION`.
- Quantized sentence-transformer paths may disable or skip gradient checkpointing if the encoder cannot support it.
- Save/export details belong in `../model-export/SKILL.md`.

## Raw Text Pretraining Or Continued LM Data Prep

Use `RawTextDataLoader` for local `.txt`, `.md`, `.json`, `.jsonl`, or `.csv` text extraction when the user asks for raw-text causal LM data prep.

```python
from unsloth import RawTextDataLoader, TextPreprocessor

preprocessor = TextPreprocessor()
loader = RawTextDataLoader(tokenizer, chunk_size=2048, stride=512, return_tokenized=True)
dataset = loader.load_from_files(["notes.txt", "docs.md"])
```

Planning notes:

- `stride` must be smaller than `chunk_size`.
- Tokenized output already contains `labels=input_ids`.
- For text-output validation, `TextPreprocessor.validate_dataset` expects a dataset with a `text` column.

## Planning-Only Output For Users

When the user asks for a recipe but not execution, return:

- selected loader class and why;
- quantization/full-finetuning choice and expected dependency implications;
- LoRA targets and any `modules_to_save` or `finetune_last_n_layers` choices;
- chat template/data field mapping;
- trainer argument sketch with `bf16`/`fp16` gate;
- exact helper commands to validate config/data;
- explicit note that training/model download is not run unless the user approves and the environment is ready.
