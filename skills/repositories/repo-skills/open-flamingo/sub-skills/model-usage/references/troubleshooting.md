# OpenFlamingo model-usage troubleshooting

Use this guide to diagnose model construction, generation, prompt, tensor, checkpoint, cache, decoder-layer, and compatibility failures.

## Fast triage checklist

1. Validate media dimensions and prompt markers with `scripts/validate_generation_inputs.py`.
2. Confirm the checkpoint family matches the language model, tokenizer, vision encoder, and `cross_attn_every_n_layers`.
3. Confirm local caches are complete before setting `use_local_files=True` or offline environment variables.
4. For generation, set `tokenizer.padding_side = "left"` and pass `attention_mask`.
5. If using `cache_media()`, pass `vision_x=None` to subsequent cached `forward()` calls and call `uncache_media()` when done.

## Symptoms and fixes

| Symptom or message | Likely cause | Fix |
| --- | --- | --- |
| `vision_x should be of shape (b, T_img, F, C, H, W)` | Media tensor is not rank 6. Common mistakes are missing the batch dimension or the frame dimension. | For one example, build `T_img x C x H x W`, then call `.unsqueeze(1).unsqueeze(0)` to get `1 x T_img x 1 x C x H x W`. |
| `Only single frame supported` | `F`/`num_frames` is not `1`. | Use `F=1`. OpenFlamingo 2.0.1 does not support multi-frame/video input in this path. |
| No image influence or blank/irrelevant completions | Prompt lacks `<image>` tokens, uses misspelled tokens, or has fewer `<image>` tokens than media items. | Use exact `<image>` tokens. Match the number of prompt media markers to the real media count for each example. |
| Generation stops immediately at a chunk boundary | Default `eos_token_id` is `<|endofchunk|>` and the prompt/model predicts it early. | This can be valid for completed chunks. For a different stop condition, pass `eos_token_id` explicitly and keep `max_new_tokens` small during tests. |
| Output includes the original prompt | `generate()` returns prompt tokens plus new tokens. | Slice `generated[:, prompt_len:]` before decoding the completion, or decode full text only for debugging. |
| Shape mismatch when using beams | Caller pre-repeated `vision_x` before `generate(num_beams=N)`. | Keep `vision_x` batch at `B`. OpenFlamingo repeats media internally for beams. |
| Assertion: `Must provide either vision_x or have precached media using cache_media().` | Standard `forward()` was called with `vision_x=None` and no cached media. | Pass `vision_x`, or call `cache_media(input_ids, vision_x)` first for cached scoring. |
| Assertion: `Expect vision_x to be None when media has been cached using cache_media(). Try uncache_media() first.` | Cached media is active and `forward()` was called with new media. | Call `model.uncache_media()` before a standard forward, or pass `vision_x=None` if using the cache. |
| `vis_x must be conditioned before forward pass` | The Flamingo layer reached cross-attention without encoded media. | Use the public `model(...)` call with valid `vision_x`, or call `cache_media()` before cached forward. Avoid calling inner language-model layers directly. |
| `media_locations must be conditioned before forward pass` | The language model was used without OpenFlamingo prompt conditioning. | Pass `lang_x` through `Flamingo.forward()` so media locations are derived from `<image>` tokens. |
| `media_location.shape is ... but x.shape is ...` | Cached or stepwise `forward()` attention masks/media locations are inconsistent with token sequence length. | For non-cached calls, `lang_x` and `attention_mask` must share `B x T_txt`; for cached one-token loops, use cached media and pass only new tokens with compatible past key values. |
| `Please supply this string manually` for decoder layers | The LM class name is not in OpenFlamingo's decoder-layer inference table. | Pass `decoder_layers_attr_name`, e.g. `model.decoder.layers`, `transformer.h`, `gpt_neox.layers`, `model.layers`, or `transformer.blocks`, depending on the LM. |
| Many missing/unexpected checkpoint keys | Wrong checkpoint family, wrapper prefix, or loading checkpoint dict wrapper directly. | If the checkpoint contains `model_state_dict`, load that value. Strip a leading `module.` prefix. Verify the exact LM/tokenizer/vision/cross-attention interval. |
| Size mismatch in `load_state_dict()` | Tokenizer/model embeddings or cross-attention layer count differ from the checkpoint. | Recreate the model with the checkpoint's language model and `cross_attn_every_n_layers`. Let `create_model_and_transforms()` add special tokens and resize embeddings before loading. |
| Cache/offline load error for tokenizer/model | `use_local_files=True`, `HF_HUB_OFFLINE=1`, or `TRANSFORMERS_OFFLINE=1` is active but cache is incomplete. | Populate the cache first with explicit network approval, or turn off offline mode. Use a caller-supplied `cache_dir` consistently for tokenizer, LM, OpenCLIP, and checkpoint. |
| Import failure with recent `transformers` and Torch 2.0.x | Newer Transformers releases may disable or reject old Torch versions. | Known compatible base: `torch==2.0.1`, `transformers==4.31.0`, and `numpy<2`. Pin versions when reproducing legacy OpenFlamingo behavior. |
| NumPy ABI or compiled-extension warnings/errors | NumPy 2.x with packages built against NumPy 1.x. | Use `numpy<2` for this package generation/eval environment. |
| Evaluation import fails for `sklearn` | Eval code imports scikit-learn, while some eval dependency declarations may omit it. | Install `scikit-learn` when running eval workflows. This is not required for the pure generation validator. |
| MPT-1B loss/training issues with `labels` | Some base MPT-1B implementations do not accept `labels` or compute CE loss as expected by OpenFlamingo training code. | Use the OpenFlamingo-compatible MPT model family associated with released 3B checkpoints for generation or training experiments. |

## Prompt/token debugging

Valid interleaved prompt properties:

- At least one `<image>` token appears in the prompt.
- The count of `<image>` tokens equals the number of real media items for that example.
- Completed demonstrations end with `<|endofchunk|>`.
- The final query usually remains open so generation can complete it.
- Tokens must be exact; `< image >`, `<image >`, or Unicode lookalikes are different text.

Examples:

```text
# One-image caption query
<image>An image of

# Two demonstrations plus one query
<image>An image of two cats.<|endofchunk|><image>An image of a sink.<|endofchunk|><image>An image of

# VQA query
<image>Question:What color is the bus? Short answer:
```

If the prompt contains multiple media items but too few `<|endofchunk|>` markers, generation may still run, but the in-context examples are ambiguous. Add chunk endings after completed examples.

## Tensor debugging

Expected image tensor lifecycle for a single example:

```python
processed_images = [image_processor(image) for image in images]  # C x H x W each
vision_x = torch.stack(processed_images, dim=0)                  # T_img x C x H x W
vision_x = vision_x.unsqueeze(1).unsqueeze(0)                    # B x T_img x F x C x H x W
```

Common corrections:

- Missing batch dimension: add `.unsqueeze(0)` at the front after stacking.
- Missing frame dimension: add `.unsqueeze(1)` between `T_img` and `C`.
- Wrong channel count: convert PIL images with `.convert("RGB")` before preprocessing.
- Device mismatch: move `vision_x`, `lang_x`, `attention_mask`, and model to the same device.
- Precision mismatch: use an explicit autocast/dtype policy only after a CPU/full-precision smoke path succeeds.

## Checkpoint debugging

Minimal robust load pattern:

```python
checkpoint = torch.load(checkpoint_path, map_location="cpu")
if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
    checkpoint = checkpoint["model_state_dict"]
if isinstance(checkpoint, dict):
    checkpoint = {key.replace("module.", "", 1): value for key, value in checkpoint.items()}
result = model.load_state_dict(checkpoint, strict=False)
print(result.missing_keys)
print(result.unexpected_keys)
```

Interpretation:

- Prefix-only unexpected keys often indicate `module.` from distributed training; strip it.
- Widespread gated cross-attention/perceiver mismatches usually mean the wrong checkpoint family or cross-attention interval.
- Embedding-size mismatches can mean the tokenizer/special-token setup does not match construction; use `create_model_and_transforms()` and do not add the tokens a second time manually.

## Cache debugging

Use `cache_media()` only for `forward()` scoring loops:

```python
try:
    model.cache_media(input_ids=context_ids, vision_x=vision_x)
    outputs = model(
        vision_x=None,
        lang_x=next_ids,
        attention_mask=None,
        clear_conditioned_layers=False,
        past_key_values=past_key_values,
        use_cache=True,
    )
finally:
    model.uncache_media()
```

Rules:

- Cached mode + `vision_x` is invalid.
- Non-cached mode + `vision_x=None` is invalid.
- `generate()` manages its own temporary media cache; call it with `vision_x`, not with pre-cached media.
- Always clear cache before switching to another image set or standard forward path.

## Import and dependency compatibility

Known working generation-oriented pins from verified dependency behavior:

```text
torch==2.0.1
transformers==4.31.0
numpy<2
```

Additional eval-oriented requirement:

```text
scikit-learn
```

If a newer dependency stack fails during import, first reproduce with the pinned baseline before debugging model code.
