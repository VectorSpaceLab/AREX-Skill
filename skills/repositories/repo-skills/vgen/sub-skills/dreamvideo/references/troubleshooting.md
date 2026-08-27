# DreamVideo troubleshooting

Use this reference when subject, motion, or joint DreamVideo runs fail before or during sampling, or when the metric helper cannot start.

## Missing or wrong base model

**Symptom:** `FileNotFoundError` or a state-dict mismatch when loading `base_model`.

**Likely cause:** the config points at the wrong checkpoint family or the file is absent.

**Fix:**

- Use the DreamVideo base checkpoint family referenced by the config, usually `models/model_scope_v1-5_0632000.pth`.
- Do not reuse a T2V/I2VGen/InstructVideo checkpoint unless the config was intentionally rewritten for it.
- Keep direct checkpoint overrides in a copied YAML so the selection is explicit.

## Subject or motion config mismatch

**Symptom:** the inference entrypoint fails while resolving adapter paths or builds the wrong log tree.

**Likely cause:** `subject_cfg` and `motion_cfg` do not match the corresponding training run, or the config was copied without updating its log-root paths.

**Fix:**

- Match each inference config to the exact subject/motion learning config that produced the adapter.
- Verify that the adapter index or path you choose belongs to the same log tree as the config.
- Keep `test_data_dir` aligned with the image root expected by the custom list.

## Conflicting adapter overrides

**Symptom:** the entrypoint raises `Both identity_adapter_index and identity_adapter_path are used` or the motion equivalent.

**Likely cause:** both forms of the same adapter override were set at once.

**Fix:**

- Use either the index form or the direct path form for each adapter type, not both.
- Prefer the index form when you are selecting a checkpoint from the training log tree.
- Prefer the path form when you already copied the adapter to a stable checkpoint location.

## Text inversion or appearance guidance problems

**Symptom:** the generated subject drifts, the subject token is ignored, or joint output looks inconsistent.

**Likely cause:** `use_textInversion` or the appearance guidance strengths are not aligned with the selected config family.

**Fix:**

- Keep `use_textInversion` enabled when the subject config expects it.
- Check `appearance_guide_strength_cond` and `appearance_guide_strength_uncond` in joint runs.
- Revisit the subject-learning config if the token or embedding is not being reused correctly.

## Metric helper dependency failures

**Symptom:** `ModuleNotFoundError` for `clip`, `dino`, `torch`, or OpenCV-related imports when running metrics.

**Likely cause:** the CLIP git package, the DINO code path, or the CUDA/OpenCV stack is missing.

**Fix:**

- Install the OpenAI CLIP package explicitly.
- Provide a valid DINO checkpoint path instead of the placeholder from the source metric file.
- Keep the metric run on a CUDA-capable environment when you want the same runtime behavior as the repository evidence.
- If the goal is only to inspect prompt-file parsing, use the bundled script's validation path first.

## Placeholder metric path

**Symptom:** the metric script references `/path/to/dino/dino_deitsmall16_pretrain.pth`.

**Likely cause:** the source metric file contains a placeholder path and expects the user to edit it.

**Fix:**

- Always pass a real DINO checkpoint path to the bundled metric helper.
- Record the checkpoint location in your own run notes rather than editing the source repository copy.

## Prompt-file format errors

**Symptom:** the metric helper cannot parse the prompts file.

**Likely cause:** the prompt file does not use exactly three fields per line.

**Fix:**

- Use `video_filename|||reference_img_folder|||text_prompt`.
- Ensure the reference folder actually contains `.jpg` images.
- Keep video filenames in sync with the generated files on disk.

## GPU, NVML, and memory issues

**Symptom:** NCCL fails, `pynvml` cannot inspect GPU 0, or the run OOMs during sampling.

**Likely cause:** the machine is not exposing CUDA/NVML correctly, or the sample is too large for the target GPU.

**Fix:**

- Use CUDA hardware; DreamVideo inference and metric work are not CPU substitutes.
- Lower `chunk_size` and `decoder_bs` before changing the model family.
- Reduce `max_frames` or simplify the custom set while debugging.
- Clear stale `MASTER_ADDR`, `MASTER_PORT`, `RANK`, and `WORLD_SIZE` values when resuming a failed distributed run.

## Stale workspace outputs

**Symptom:** joint or metric runs appear to read the wrong videos or reference folders.

**Likely cause:** the output tree already contains files from an older run with the same caption stem.

**Fix:**

- Start from a fresh log directory for each comparison pass.
- Delete or move stale outputs before rerunning a prompt set.
- Keep one subject/motion experiment per workspace while debugging.

## Adapter-key helper failures

**Symptom:** `scripts/dump_adapter_keys.py` cannot import the model or returns an empty key list.

**Likely cause:** the repo checkout is missing optional modules, or the selected config builds a model that does not use the expected temporal/spatial blocks.

**Fix:**

- Confirm the repo root and config path are correct.
- Make sure the VGen runtime imports succeed before requesting the key export.
- If the key list is empty, re-check whether the selected config family actually uses the adapter-friendly blocks you expected.
