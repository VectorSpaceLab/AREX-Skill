# Qwen2.5-VL API reference

This reference focuses on the Qwen-specific pieces that sit on top of Maestro's shared dataset and metric helpers.

## Constants and enums

```python
DEFAULT_QWEN2_5_VL_MODEL_ID = "Qwen/Qwen2.5-VL-3B-Instruct"
DEFAULT_QWEN2_5_VL_MODEL_REVISION = "refs/heads/main"
DEFAULT_QWEN2_5_VL_PEFT_PARAMS = {
    "r": 8,
    "lora_alpha": 16,
    "lora_dropout": 0.05,
    "bias": "none",
    "target_modules": ["q_proj", "v_proj"],
    "task_type": "CAUSAL_LM",
}
```

```python
class OptimizationStrategy(Enum):
    LORA = "lora"
    QLORA = "qlora"
    NONE = "none"
```

## Configuration and training

### `Qwen25VLConfiguration`

```python
Qwen25VLConfiguration(
    dataset: str,
    model_id: str = "Qwen/Qwen2.5-VL-3B-Instruct",
    revision: str = "refs/heads/main",
    device: str | torch.device = "auto",
    optimization_strategy: Literal["lora", "qlora", "none"] = "lora",
    epochs: int = 10,
    lr: float = 2e-4,
    batch_size: int = 4,
    accumulate_grad_batches: int = 8,
    val_batch_size: Optional[int] = None,
    num_workers: int = 0,
    val_num_workers: Optional[int] = None,
    output_dir: str = "./training/qwen_2_5_vl",
    metrics: list[BaseMetric] | list[str] = field(default_factory=list),
    system_message: Optional[str] = None,
    min_pixels: int = 256 * 28 * 28,
    max_pixels: int = 1280 * 28 * 28,
    max_new_tokens: int = 1024,
    random_seed: Optional[int] = None,
    peft_advanced_params: Optional[dict] = None,
)
```

Key behavior:

- Fills `val_batch_size` from `batch_size` when omitted.
- Fills `val_num_workers` from `num_workers` when omitted.
- Converts string metric names with `parse_metrics(...)`.
- Normalizes `device` with `parse_device_spec(...)` and raises if the device is unavailable.
- Carries `system_message`, `min_pixels`, and `max_pixels` through to the collators and processor.

### `train(config: Qwen25VLConfiguration | dict) -> None`

- Accepts either a config dataclass or a plain dictionary.
- Dictionary inputs are converted with `dacite.from_dict(...)`.
- The trainer creates a fresh run directory, loads the model, builds data loaders, runs Lightning training, and saves checkpoints plus metric plots.
- `dataset` can be a local path or a resolvable Roboflow identifier.

## Checkpoint loading and saving

### `load_model(...)`

```python
load_model(
    model_id_or_path: str = "Qwen/Qwen2.5-VL-3B-Instruct",
    revision: str = "refs/heads/main",
    device: str | torch.device = "auto",
    optimization_strategy: OptimizationStrategy = OptimizationStrategy.NONE,
    peft_advanced_params: Optional[dict] = None,
    cache_dir: Optional[str] = None,
    min_pixels: int = 256 * 28 * 28,
    max_pixels: int = 1280 * 28 * 28,
) -> tuple[Qwen2_5_VLProcessor, Qwen2_5_VLForConditionalGeneration]
```

Behavior:

- Loads the processor with `min_pixels` / `max_pixels` and left-padding enabled.
- `lora` and `qlora` wrap the model in PEFT `LoraConfig` using the default target modules `q_proj` and `v_proj`.
- `qlora` also loads the base model with a 4-bit `BitsAndBytesConfig`.
- `none` loads the base model without PEFT wrapping and then moves it to the selected device.
- `peft_advanced_params` is merged into the default LoRA configuration before the PEFT wrapper is created.
- `Qwen25VLConfiguration` defaults to `lora`, while `load_model(...)` defaults to `OptimizationStrategy.NONE`; set both explicitly if you want the same strategy in training and later checkpoint loading.

### `save_model(target_dir, processor, model) -> None`

- Creates the target directory if needed.
- Saves the processor and model with `save_pretrained(...)`.
- Use it for the checkpoint callback output, not for downloading a fresh model.

## Conversation and collators

### `format_conversation(...)`

```python
format_conversation(
    image: str | bytes | Image.Image,
    prefix: str,
    suffix: str | None = None,
    system_message: str | None = None,
) -> list[dict]
```

Behavior:

- Emits a Qwen chat list.
- Optional `system_message` is placed in a leading `system` turn.
- The user turn contains the image and the text prefix.
- If `suffix` is provided, it becomes the supervised assistant turn.

### `train_collate_fn(batch, processor, system_message=None)`

- Consumes `(image, entry)` pairs.
- Builds full conversations with `format_conversation(...)`.
- Renders text with `processor.apply_chat_template(..., tokenize=False)`.
- Uses `process_vision_info(...)` and `processor(...)` to build tensors.
- Masks pad tokens and the image-token IDs `151652`, `151653`, and `151655`.
- Masks the prompt portion before the assistant suffix so loss is only computed on the target text.

### `evaluation_collate_fn(batch, processor, system_message=None)`

- Same prompt construction as training, but without the assistant suffix.
- Returns the tensors plus the original images, prefixes, and suffixes so validation can compute text and detection metrics.

## Inference

### `predict_with_inputs(...)`

```python
predict_with_inputs(
    model,
    processor,
    input_ids,
    attention_mask,
    pixel_values,
    image_grid_thw,
    device,
    max_new_tokens: int = 1024,
) -> list[str]
```

- Batched generation helper used by validation.
- Calls `model.generate(...)`, strips the prompt tokens, and decodes the generated suffixes.

### `predict(...)`

```python
predict(
    model,
    processor,
    image,
    prefix,
    system_message: str | None = None,
    device: str | torch.device = "auto",
    max_new_tokens: int = 1024,
) -> str
```

Behavior:

- Builds a conversation with `format_conversation(...)`.
- Renders the conversation with `processor.apply_chat_template(..., tokenize=False, add_generation_prompt=True)`.
- Uses `process_vision_info(...)` to prepare image inputs.
- Returns one decoded string.
- This is the safest API when you already have a single image and prompt.

## Detection formatters

### `detections_to_prefix_formatter(...)`

```python
detections_to_prefix_formatter(
    xyxy: np.ndarray,
    class_id: np.ndarray,
    classes: list[str],
    resolution_wh: tuple[int, int],
) -> str
```

- Returns the detection prompt prefix.
- The prompt names the classes and asks for JSON coordinates.
- The helper is model-specific; COCO dataset loading and class extraction belong to the sibling dataset skill.

### `detections_to_suffix_formatter(...)`

```python
detections_to_suffix_formatter(
    xyxy: np.ndarray,
    class_id: np.ndarray,
    classes: list[str],
    resolution_wh: tuple[int, int],
    min_pixels: int,
    max_pixels: int,
) -> str
```

Behavior:

- Calls `qwen_vl_utils.smart_resize(...)` to determine the resized input dimensions.
- Rescales each box from original image coordinates into the resized input space.
- Casts coordinates to integers.
- Returns a fenced JSON array of objects with `bbox_2d` and `label`.

## Practical defaults to remember

- Qwen JSON extraction usually uses a task-specific `system_message` that tells the model to emit JSON only.
- Object-detection recipes often use a neutral or short system message and keep the pixel bounds identical at train, load, and inference time.
- If the CLI receives `--peft_advanced_params`, it expects a JSON object string.
