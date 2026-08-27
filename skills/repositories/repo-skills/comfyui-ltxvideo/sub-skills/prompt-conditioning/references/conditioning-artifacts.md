# Conditioning Artifacts

`LTXVSaveConditioning` and `LTXVLoadConditioning` let a workflow cache expensive positive/negative prompt conditioning as safetensors files. This is useful when prompts, Gemma/API encoding, or prompt enhancement are the slow or credential-sensitive part of repeated workflow runs.

For root install and model-folder expectations, see the [model and backend requirements](../../../references/model-and-backend-requirements.md).

## Save node

`LTXVSaveConditioning` is an output node with required inputs:

- `conditioning`: the ComfyUI `CONDITIONING` list to save.
- `filename`: base name; default `conditioning`.
- `dtype`: `bfloat16` or `float16`.

Behavior:

1. The node rejects missing or empty conditioning with:

   ```text
   Conditioning is empty
   ```

2. It writes into ComfyUI's first configured `embeddings` folder, creating it if needed.
3. It sanitizes `filename`, keeping only letters, numbers, `_`, `-`, and `.`. If nothing remains, it falls back to `conditioning`.
4. It writes `<sanitized_filename>.safetensors`.
5. Each conditioning entry is converted to the requested dtype and saved as `conditioning_data_<index>`.
6. If a conditioning entry has an `attention_mask` option, the mask is saved as `attention_mask_<same_index>`.
7. Metadata includes `num_conditionings`, `dtype`, and `created_at`.

## Load node

`LTXVLoadConditioning` has required inputs:

- `file_name`: selected from ComfyUI `embeddings` files.
- `device`: `cpu` or `gpu`.

Behavior:

1. If no embedding files are listed, input validation returns:

   ```text
   No files found. Please save a conditioning first.
   ```

2. Missing files fail as either:

   ```text
   File not found: <file_name>
   Conditioning file not found: <resolved file>
   ```

3. Invalid file lookup fails as:

   ```text
   Invalid file: <file_name>
   ```

4. `device=cpu` opens the safetensors file on CPU.
5. `device=gpu` opens on CUDA only when CUDA is available; otherwise it falls back to CPU.
6. Keys beginning with `conditioning_data_` are read back into a ComfyUI conditioning list.
7. Matching `attention_mask_<index>` keys are restored into each conditioning entry's options.
8. If no `conditioning_data_*` keys exist, loading raises:

   ```text
   No conditioning data found in file: <file_name>
   ```

## Safetensors layout

A valid saved file has one or more data tensors and optional attention masks:

```text
conditioning_data_0        # required
attention_mask_0           # optional, only if options contained attention_mask
conditioning_data_1        # optional additional conditioning entry
attention_mask_1           # optional matching mask
...
```

The load node pairs masks by suffix. `attention_mask_2` belongs to `conditioning_data_2`. Orphan attention masks indicate a suspicious or hand-edited file and should be fixed before use.

Use the bundled validator from this sub-skill before reusing artifacts from another machine or from manual edits:

```bash
python ../scripts/validate_conditioning_safetensors.py <path-to-conditioning.safetensors>
```

Run from this `references/` directory as shown above, or adjust the relative path from your current directory. The script only opens the safetensors file for metadata/key/tensor inspection; it does not run ComfyUI, download models, or execute generation.

## Dtype tradeoffs

Both supported dtypes are 16-bit formats and have similar storage size; choose based on compatibility and numerical behavior:

- `bfloat16`: matches the local Gemma/LTX text-embedding pipeline's common dtype and keeps a wider exponent range. Prefer it when the downstream LTX model and hardware support bfloat16 well.
- `float16`: broadly supported on many CUDA workflows and may match older graph expectations. Prefer it when a downstream node or external tool cannot handle bfloat16.

If loaded conditioning appears numerically unstable or downstream nodes reject dtype, regenerate and save with the other dtype. Do not convert by hand unless you also preserve key names and attention-mask pairing.

## Device tradeoffs

- Load on `cpu` when you want lower VRAM pressure, are validating files, or expect downstream model loading to move tensors as needed.
- Load on `gpu` only when CUDA is available and the workflow benefits from keeping conditioning on the GPU. This can reduce transfers but consumes VRAM before sampling.
- If `device=gpu` silently behaves like CPU on a non-CUDA host, that is source-backed fallback behavior, not proof that native generation can run without CUDA.

## Reuse recipe

1. Build or load the prompt encoder path once: local Gemma, API encoder, or prompt enhancer plus encoder.
2. Produce the exact positive/negative `CONDITIONING` objects needed by the target graph.
3. Save each reusable conditioning branch with a descriptive, sanitized filename.
4. Validate the created safetensors file with `validate_conditioning_safetensors.py`.
5. In later workflows, replace the prompt encoder branch with `LTXVLoadConditioning` nodes that load the saved positive/negative artifacts.
6. Keep the LTX model/checkpoint family consistent. Reusing conditioning across incompatible LTX versions or video/audio variants can fail later in guider/sampler code even if the safetensors file itself validates.

## What the validator can and cannot prove

The validator can prove:

- the file exists and has a `.safetensors` extension or a consciously accepted custom suffix;
- at least one `conditioning_data_<index>` tensor is present;
- optional masks use numeric suffixes and are paired with data tensors;
- tensors can be read on CPU;
- shapes, dtypes, and metadata are visible.

The validator cannot prove:

- the conditioning semantically matches a particular prompt;
- the conditioning belongs to the selected LTX checkpoint family;
- a full ComfyUI generation workflow will fit in VRAM;
- API credentials or local Gemma model placement are valid.
