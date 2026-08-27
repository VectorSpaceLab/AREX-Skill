# Model-module troubleshooting

Use this guide for VLM-R1 failures that arise before or inside the module layer. If the problem is mostly launch flags, data schema, generic reward math, or evaluation output scoring, route it to the sibling sub-skill named for that area.

## Quick triage

| Symptom | Likely module-layer cause | First check |
| --- | --- | --- |
| `Unsupported model: ...` | Substring routing did not match `qwen`, `internvl`, or `glm`; or new backend was not added to routing. | Confirm the model id contains the intended lower-case key or add a routing branch. |
| Qwen id routes but raises unsupported model | Qwen module only accepts ids containing `Qwen2-VL` or `Qwen2.5-VL`. | Check exact model family string. |
| InternVL import/load complains about remote code | InternVL module requires `trust_remote_code=True` and uses `AutoModel` remote code. | Ensure the model-loading kwargs preserve `trust_remote_code=True`. |
| `image_flags` passed to `generate` fails | InternVL-specific `image_flags` must be removed before generation. | `get_non_generate_params()` must include `image_flags`. |
| Forward/log-prob call misses image tensors | `get_custom_multimodal_keywords()` does not match processor output keys. | Qwen/GLM use `pixel_values`, `image_grid_thw`; InternVL uses `pixel_values`, `image_flags`. |
| REC custom reward cannot find `image_grid_thw` | Qwen/GLM reward expects per-example image-grid metadata from `prepare_model_inputs`. | Ensure image batches produce `additional_output` containing `image_grid_thw`. |
| Freeze vision does nothing | Freeze keyword does not match parameter names. | Qwen/GLM use `visual`; InternVL uses `vision_model`; inspect parameter names in the working copy. |
| Pixel or any-res limits ignored | Custom processing keyword is attached to the wrong processor component. | Qwen/GLM set `image_processor.max_pixels/min_pixels`; InternVL sets processor-level `max_anyres_num`. |
| `Glm4vForConditionalGeneration` import error | Pinned Transformers 4.49.0 lacks that class. | See the GLM section below. |

## `ImportError: cannot import name 'Glm4vForConditionalGeneration'`

What it means:

- GLM support is present in the module layer, but the inspected repository environment used Transformers 4.49.0.
- That version does not provide `Glm4vForConditionalGeneration`.
- A package-level VLM-module import pulls in the GLM module, so the failure can appear even when the immediate user task is Qwen or InternVL.

Safe remedies:

1. If the user is not actually using GLM, avoid eager GLM import in the working copy. Prefer a guarded or lazy import that raises a GLM-specific message only when the GLM route is selected.
2. If the user needs GLM, install or pin a Transformers version known to expose `Glm4vForConditionalGeneration`, then rerun import and a minimal model-class smoke check.
3. After GLM import succeeds, verify the GLM EOS hook signature matches the trainer call shape before starting training.
4. Do not claim GLM readiness from static code presence alone.

## Adding `myvlm` but routing still picks another module

Likely causes:

- The model id contains an earlier-matched substring such as `qwen`.
- The routing branch for `myvlm` was not added or is below an overly broad branch.
- Exports/imports do not make `MyVLMModule` available to the training entry point.

Fix pattern:

```python
def get_vlm_module(model_name_or_path):
    name = model_name_or_path.lower()
    if "myvlm" in name:
        return MyVLMModule
    if "qwen" in name:
        return Qwen2VLModule
    if "internvl" in name:
        return InvernVLModule
    if "glm" in name:
        return GLMVModule
    raise ValueError(f"Unsupported model: {model_name_or_path}")
```

Then run the static checker with `--expect-key myvlm --strict`.

## Processor input-key mismatches

The trainer needs two different key sets:

- Generate inputs: `prompt_inputs` minus keys returned by `get_non_generate_params()`.
- Forward/log-prob multimodal inputs: keys returned by `get_custom_multimodal_keywords()`.

Expected module behavior:

| Module | `get_custom_multimodal_keywords()` | `get_non_generate_params()` | Notes |
| --- | --- | --- | --- |
| Qwen2VL | `pixel_values`, `image_grid_thw` | empty | `image_grid_thw` may also be passed to REC reward through `additional_output`. |
| InternVL | `pixel_values`, `image_flags` | `image_flags` | `image_flags` is needed for forward/log-prob but should not go to `generate`. |
| GLM | `pixel_values`, `image_grid_thw` | empty | GLM import must be repaired before runtime use. |

If generation succeeds but loss/log-probs fail, focus on `get_custom_multimodal_keywords()`. If generation itself fails on an unexpected keyword, focus on `get_non_generate_params()`.

## Prompt-template and output-format issues

The data loader always formats questions through the module class. If a new `task_type` yields poor or invalid answers:

1. Add or adjust `get_question_template(task_type)` in the module.
2. Keep `{Question}` in the returned string.
3. Align the template with reward expectations:
   - all current modules use `<think>` and `<answer>` tags;
   - Qwen REC format expects a JSON-style final answer containing a bbox;
   - InternVL REC format expects a bracketed bbox in `<answer>` tags;
   - generic format reward only checks `<think>...</think><answer>...</answer>`.
4. Route generic reward registry selection details to `../data-and-rewards/`.

## Custom reward hook errors

When `is_reward_customized_from_vlm_module` is enabled, every reward name is resolved through the selected module's `select_reward_func(func, task_type)`. Failures usually mean one of these:

- The reward name is generic but not implemented in the module hook.
- The task type is not handled by the module hook.
- The module reward expects metadata that `prepare_model_inputs` did not add.
- The answer template and reward parser disagree.

Safe fix:

- Keep generic rewards generic unless the module needs special metadata or parsing.
- For REC custom rewards, test both a valid and malformed completion.
- Ensure Qwen/GLM REC rewards receive `image_grid_thw` and image path metadata when they need coordinate resizing.

## Freeze-vision surprises

`freeze_vision_modules` freezes parameters whose names contain any substring returned by `get_vision_modules_keywords()`. It also uses the same vision keywords to avoid applying LoRA to vision modules.

Known keywords:

- Qwen2VL and GLM: `visual`.
- InternVL: `vision_model`.

If too much or too little freezes:

1. Print or inspect representative `named_parameters()` names in the working copy.
2. Narrow the keyword if it also matches language-side parameters.
3. Broaden it only if all vision-side parameters share the substring.
4. Recheck LoRA target-module selection after changing freeze keywords.

## Pixel limit and any-resolution failures

- Qwen/GLM pixel controls live on `processing_class.image_processor`:
  - `max_pixels` default: `12845056`.
  - `min_pixels` default: `3136`.
- InternVL any-resolution control lives on the processor itself:
  - `max_anyres_num` default: `12`.

Symptoms and fixes:

- Images are too small: the trainer resizes dimensions under 28 pixels before module processing, but custom processors may still enforce their own minimums.
- Qwen OOM: lower `max_pixels` through the training workflow.
- InternVL OOM or too many patches: lower `max_anyres_num`.
- InternVL assertion about image count: prompt `<image>` placeholders must match the flattened image list.

## Static checker failures

Run:

```bash
python scripts/inspect_model_module_contract.py path/to/module.py --strict
```

Interpretation:

- `missing_required`: the class is not instantiable or cannot satisfy the base trainer contract.
- `missing_runtime`: the GRPO entry point will likely fail, usually due to a missing `get_question_template`.
- `missing_recommended`: the class may rely on base defaults or lack custom rewards; decide explicitly before full integration.
- `detected_key`: the checker could statically read a simple `return "key"` from `get_vlm_key`.

For a new module, do not proceed to launch-command work until required and runtime failures are resolved.

## Known hard cases to test mentally

1. **Adding `myvlm`**: user supplies a new module with model class and processor but forgets `get_non_generate_params`, `get_question_template`, and routing. The correct response is to list the missing contract pieces, add a routing branch and export, then rerun the static checker with `--expect-key myvlm --strict`.
2. **Diagnosing GLM import**: user reports `ImportError: Glm4vForConditionalGeneration`. The correct response is to explain the Transformers 4.49.0 mismatch, avoid eager GLM imports for non-GLM tasks, and require a compatible Transformers version plus smoke checks before GLM training.
