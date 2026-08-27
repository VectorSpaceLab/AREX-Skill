# VLM-R1 model-module contract

This reference distills the VLM-R1 module layer used by the GRPO trainer. It is self-contained: use it to implement or review a working-copy module without reopening repository source as background reading.

## Where model modules fit

The training entry point chooses a VLM module from the configured `model_name_or_path`, asks that module for model and processor classes, then delegates prompt formatting, processor calls, generation input filtering, multimodal forward inputs, question templates, and optional module-specific rewards.

Model-name routing is substring based:

| Model name contains | Module class | Status |
| --- | --- | --- |
| `qwen` | `Qwen2VLModule` | Supported for Qwen2-VL and Qwen2.5-VL when model id contains the expected family string. |
| `internvl` | `InvernVLModule` | Supported through remote-code `AutoModel`/`AutoProcessor` conventions. Note the class name is spelled `InvernVLModule` in the code. |
| `glm` | `GLMVModule` | Present but import-blocked in the pinned Transformers 4.49.0 environment because `Glm4vForConditionalGeneration` is absent. Treat as unverified. |
| anything else | none | Raises `ValueError("Unsupported model: ...")`. |

## Required module methods

A new VLM module should subclass the base module and deliberately implement the full operational contract below. The abstract base only enforces the core methods, but the GRPO entry point also expects prompt-template hooks; explicit defaults avoid surprises.

| Method | Required for | What it must return or do |
| --- | --- | --- |
| `get_vlm_key(self)` | Module identity | Short routing key such as `qwen`, `internvl`, or `myvlm`. |
| `get_model_class(self, model_id, model_init_kwargs)` | Model loading | Return a class with `from_pretrained`; mutate `model_init_kwargs` only for backend-required settings such as `trust_remote_code`. |
| `post_model_init(self, model, processing_class)` | Backend setup | Set backend-specific fields after model and processor construction; no-op is acceptable for Qwen-like modules. Guard `model is None` if reference models may be disabled. |
| `is_embeds_input(self)` | Generation post-processing | Return `True` if `generate` returns only completion ids because the model consumed prompt embeddings; return `False` for normal `input_ids` generation. |
| `get_processing_class(self)` | Processor loading | Return a processor/tokenizer class, usually `AutoProcessor`. |
| `get_vision_modules_keywords(self)` | LoRA exclusion and `freeze_vision_modules` | Return substrings matched against parameter names for vision modules. |
| `get_custom_multimodal_keywords(self)` | Forward/log-prob inputs | Return non-text tensor keys to pass into forward log-prob calls. |
| `get_non_generate_params(self)` | Generation input filtering | Return keys present in processor output that must not be sent to `generate`. |
| `get_custom_processing_keywords(self)` | Runtime processor limits | Return `(component, attribute)` pairs set from trainer keyword args, e.g. `('image_processor', 'max_pixels')`. Use component `None`/`'None'` to mean the processor itself. |
| `prepare_prompt(self, processing_class, inputs)` | Chat template | Convert conversation examples into prompt strings compatible with the model processor. |
| `prepare_model_inputs(self, processing_class, prompts_text, images, return_tensors, padding, padding_side, add_special_tokens)` | Processor call | Return `(prompt_inputs, additional_output)`, where `prompt_inputs` contains `input_ids`, `attention_mask`, and backend multimodal keys; `additional_output` may add per-example reward metadata. |
| `get_question_template(task_type)` | JSONL-to-chat conversion | Return a template containing `{Question}`. The training entry point calls this for every dataset example. |
| `select_reward_func(func, task_type)` | Custom module rewards | Return a callable when `is_reward_customized_from_vlm_module` is enabled; raise a clear error for unsupported combinations. |

## Qwen2VL / Qwen2.5-VL behavior

- Key: `qwen`.
- Model class:
  - `Qwen2VLForConditionalGeneration` when the model id contains `Qwen2-VL`.
  - `Qwen2_5_VLForConditionalGeneration` when the model id contains `Qwen2.5-VL`.
  - Any other Qwen-looking id raises an unsupported-model error.
- Processor class: `AutoProcessor`.
- Post-init: no-op.
- Embedding input: `False`; generation returns prompt plus completion ids.
- Freeze/LoRA vision keyword: `visual`.
- Custom multimodal forward keys: `pixel_values`, `image_grid_thw`.
- Non-generate keys: none.
- Custom processor settings:
  - `image_processor.max_pixels` from `max_pixels`.
  - `image_processor.min_pixels` from `min_pixels`.
  - Defaults used by the training arguments are `max_pixels=12845056` and `min_pixels=3136`.
- Prompt preparation: applies the model chat template to each example and returns the resulting `prompt` text.
- Model input preparation:
  - With images, calls the processor with `text=prompts_text`, `images=images`, padding, and tensor settings.
  - Without images, calls the processor with text only.
  - When images are present, returns per-example `additional_output` containing `image_grid_thw`; Qwen REC IoU reward uses it to map predicted coordinates back to image size.
  - The source implementation notes it handles homogeneous pure-multimodal or pure-text batches; avoid mixed image/text-only samples in one batch unless you adapt this logic.
- Question templates:
  - `rec`: asks for reasoning in `<think>` tags and JSON final answer in `<answer>` tags.
  - `ic`: asks for `<think>` and `<answer>` with JSON-format answer.
  - `odLength`: prepends a system-style reasoning instruction, then `{Question}`.
  - default: asks for `<think>` and `<answer>` tags.
- Module custom rewards:
  - `accuracy` + `rec` -> Qwen REC IoU reward.
  - `format` + `rec` -> Qwen REC format reward.
  - Other combinations raise unsupported-reward errors.

## InternVL behavior

- Key: `internvl`.
- Class name in this repository: `InvernVLModule`.
- Model class: `AutoModel`; the model config determines the concrete class.
- Model init mutations:
  - Requires model id containing `InternVL`.
  - Loads config with `trust_remote_code=True`.
  - Sets `model_init_kwargs['trust_remote_code'] = True`.
  - Removes `use_cache`.
  - Converts `attn_implementation='flash_attention_2'` into `use_flash_attn=True` for InternVL remote code.
- Processor class: `AutoProcessor`.
- Post-init:
  - Caches `model.conv_template` and `model.num_image_token`.
  - Converts `<IMG_CONTEXT>` to an id and assigns `model.img_context_token_id`.
  - If adapting this module, guard against `model is None` when reference-model creation is disabled.
- Embedding input: `True`; `generate` returns completion ids only, so the trainer concatenates prompt ids manually for log-prob computation.
- EOS hook: derives EOS from `conv_template.sep`.
- Freeze/LoRA vision keyword: `vision_model`.
- Custom multimodal forward keys: `pixel_values`, `image_flags`.
- Non-generate keys: `image_flags`; keep this out of `generate` calls.
- Custom processor setting:
  - `max_anyres_num` is set on the processor itself.
  - Default used by training arguments is `max_anyres_num=12`.
- Prompt preparation:
  - Converts chat content lists into strings.
  - Image content becomes `<image>\n`.
  - Text content is appended as text.
  - A leading system message becomes the conversation template system message.
  - If the conversation ends with a user turn, appends an empty assistant turn.
- Model input preparation:
  - Loads each image into dynamic any-resolution patches using the configured vision image size and `max_anyres_num`.
  - Replaces each `<image>` placeholder with `<img>` + repeated `<IMG_CONTEXT>` tokens + `</img>` according to patch count and `num_image_token`.
  - Concatenates all image patch tensors into `pixel_values`.
  - Adds `image_flags` of ones for each patch.
  - Returns a `BatchFeature` with text tokens plus `pixel_values` and `image_flags`.
  - The implementation is for image-bearing data; text-only batches need an explicit adaptation.
- Question templates:
  - default template only: `{Question}` plus `<think>`/`<answer>` instruction.
- Module custom rewards:
  - `accuracy` + `rec` -> InternVL REC IoU reward.
  - `format` + `rec` -> InternVL REC format reward.
  - InternVL REC answer format is a bracketed bbox in `<answer>` tags, not necessarily a JSON object.

## GLM boundary

`GLMVModule` mirrors Qwen-style processor inputs (`pixel_values`, `image_grid_thw`), freeze keyword `visual`, and `max_pixels`/`min_pixels` processor settings. It also provides `glm` routing and REC custom rewards.

However, the inspected environment pins Transformers 4.49.0, and that package does not expose `Glm4vForConditionalGeneration`. Because the package-level VLM module import includes GLM, this can block broad imports even for workflows that are not using GLM. Do not treat GLM as available unless you first prove a compatible Transformers version or a guarded/lazy GLM import. Also check the GLM EOS hook signature before training; it should match how the trainer calls module EOS hooks.

## Custom prompt and reward hooks

The data loader builds a conversation by formatting the first user problem through the selected module class:

```python
question_prompt = ModuleClass.get_question_template(task_type=task_type)
question_prompt.format(Question=problem)
```

When `is_reward_customized_from_vlm_module` is false, reward names come from the generic registry. When it is true, each reward name is resolved by:

```python
ModuleClass.select_reward_func(func, task_type)
```

Use module-specific rewards only when the model's output format or required metadata differs from the generic registry. For REC rewards, keep the answer template, bbox parser, and `additional_output` metadata aligned. Qwen/GLM REC rewards expect `image_grid_thw` and image paths for coordinate resizing; InternVL REC reward compares raw bbox coordinates.

## Add a new model backend checklist

For a new `myvlm` backend:

1. Create a module class that subclasses the base module and implements every method in the contract table.
2. Choose a stable key, e.g. `myvlm`, and make `get_vlm_key()` return it.
3. Decide model-loading behavior:
   - concrete Transformers class vs `AutoModel`;
   - whether `trust_remote_code` is required;
   - whether `use_cache`, `attn_implementation`, or dtype kwargs need backend-specific changes.
4. Decide processor behavior:
   - processor class;
   - processor attributes controlled by `max_pixels`, `min_pixels`, `max_anyres_num`, or new settings;
   - exact output keys and shapes.
5. Decide generation behavior:
   - normal `input_ids` generation or embedding-input generation;
   - any keys to exclude from `generate`;
   - any custom EOS hook.
6. Decide freeze keywords using actual parameter-name substrings; verify they do not match unrelated language modules.
7. Implement `prepare_prompt` and `prepare_model_inputs` for the dataset shapes you plan to support: text-only, single-image, multi-image, or mixed batches.
8. Implement `get_question_template` for the task types you will train.
9. Implement `select_reward_func` only for module-specific rewards; otherwise keep users on generic rewards.
10. Update module exports and model-name routing so `model_name_or_path` containing `myvlm` resolves to your class.
11. Run `scripts/inspect_model_module_contract.py` with `--strict` on the new module or module directory.
12. Hand training command construction to the training-workflows sub-skill after the module contract passes.

## Static checker expectations

`inspect_model_module_contract.py` performs AST-only checks. It reports:

- classes that appear to be VLM modules;
- missing abstract/base contract methods;
- missing runtime hooks such as `get_question_template`;
- missing recommended decision hooks such as `post_model_init`, `is_embeds_input`, and `select_reward_func`;
- detected simple `get_vlm_key()` return strings.

Use `--strict` when reviewing a new backend intended for full VLM-R1 GRPO integration.
