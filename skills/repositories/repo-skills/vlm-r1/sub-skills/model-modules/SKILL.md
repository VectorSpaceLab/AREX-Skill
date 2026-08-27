---
name: model-modules
description: "Add and debug VLM-R1 model modules, including Qwen2VL, InternVL,
  GLM boundaries, processor inputs, freeze keywords, and custom reward hooks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# VLM-R1 model modules

Use this sub-skill when a task is about adding, adapting, or debugging a VLM backend used by VLM-R1 GRPO training. This skill is intentionally router-like: use the references for the actual contract and failure details.

## Route first

- Use this skill for:
  - adding a new module such as `myvlm`;
  - diagnosing model-name routing (`qwen`, `internvl`, `glm`);
  - checking processor/model input keys (`pixel_values`, `image_grid_thw`, `image_flags`);
  - choosing freeze-vision keywords;
  - understanding Qwen2VL, InternVL, and GLM support boundaries;
  - implementing module-level `get_question_template` or `select_reward_func` hooks.
- Route GRPO launch flags, DeepSpeed, LoRA command lines, multi-node, and W&B options to `../training-workflows/`.
- Route generic JSONL schemas, global reward names, bbox scoring concepts, and non-module reward debugging to `../data-and-rewards/`.
- Route saved REC/OVD evaluation output scoring to `../evaluation/`.

## Required workflow

1. Read `references/model-modules.md` for the module contract and backend-specific differences.
2. If editing or reviewing a module source file, run the no-import checker:

   ```bash
   python scripts/inspect_model_module_contract.py path/to/module.py --strict
   ```

   For a directory of module files, run:

   ```bash
   python scripts/inspect_model_module_contract.py path/to/vlm_modules --strict
   ```

3. For an added model backend, verify all of the following are deliberately handled before touching training launch commands:
   - subclass/interface methods;
   - model-name routing branch;
   - package exports/imports;
   - processor input keys and non-generate keys;
   - freeze-vision keywords;
   - prompt template for the requested `task_type`;
   - custom rewards only if `is_reward_customized_from_vlm_module` will be used.
4. If an error mentions GLM import or `Glm4vForConditionalGeneration`, use `references/troubleshooting.md` before assuming a broken checkpoint.

## Fast decisions

- Qwen2-VL/Qwen2.5-VL: Qwen-style processor inputs with `pixel_values` and `image_grid_thw`; freeze keyword `visual`; pixel bounds are `max_pixels` and `min_pixels`.
- InternVL: remote-code AutoModel/AutoProcessor path; generation uses embeddings; processor/model inputs include `pixel_values` and `image_flags`; exclude `image_flags` from `generate`; freeze keyword `vision_model`; any-resolution cap is `max_anyres_num`.
- GLM: code exists, but the pinned Transformers environment used for this repository did not expose `Glm4vForConditionalGeneration`; treat GLM as unverified until imports and signatures are repaired.

## Bundled files

- `references/model-modules.md` — complete distilled module contract, Qwen vs InternVL behavior, GLM caveats, and add-new-model checklist.
- `references/troubleshooting.md` — diagnosis recipes for routing, imports, processor key mismatches, freezing, pixel bounds, and custom rewards.
- `scripts/inspect_model_module_contract.py` — static AST checker for module files/directories; it never imports the repository.
