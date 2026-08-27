# Inference Workflows

## Purpose

Read this when you need a concrete HunyuanVideo-I2V generation recipe. The bundled script can print or execute the exact command, but this reference explains the intent behind the main modes.

## 1) Stable single-image generation

Use this when the user wants a coherent video with minimal drift.

Key settings:

- `--i2v-mode`
- `--i2v-stability`
- `--flow-shift 7.0`
- `--flow-reverse`
- `--embedded-cfg-scale 6.0`
- `--use-cpu-offload` for large resolutions or small GPUs

Typical dry-run pattern (run from the real checkout root; `$SKILL_ROOT` is the generated skill directory, not the checkout):

```bash
cd "$CHECKOUT_ROOT"
python "$SKILL_ROOT/sub-skills/inference/scripts/run_sample_image2video.py" \
  --repo-root "$CHECKOUT_ROOT" \
  --mode stable \
  --prompt "..." \
  --image-path "$CHECKOUT_ROOT/assets/demo/i2v/imgs/0.png" \
  --save-path "$CHECKOUT_ROOT/results" \
  --dry-run
```

`--repo-root` must point to the checkout containing `sample_image2video.py`; it must not point to `$SKILL_ROOT`. The wrapper only prints this command unless `--execute` is supplied.

## 2) Dynamic motion generation

Use this when the user wants more movement or scene change.

Key settings:

- same as stable mode, but omit `--i2v-stability`
- `--flow-shift 17.0`

The bundled wrapper can switch modes with `--mode dynamic`.

## 3) LoRA-augmented inference

Use this when the user has a trained LoRA weight and wants to apply a special effect.

Key settings:

- `--use-lora`
- `--lora-path "$CHECKOUT_ROOT/ckpts/.../*.safetensors"`
- `--lora-scale 1.0`
- keep the same image/prompt/resolution choices as the base inference flow

Pass the LoRA path only when a real `.safetensors` file exists; the repository does not ship or fabricate adapter weights.

If the LoRA is not yet trained, send the user to the `lora-training` sub-skill first.

## 4) xDiT / multi-GPU inference

Use this when the user explicitly wants sequence-parallel speedup across multiple GPUs.

Key settings:

- `--ulysses-degree N`
- `--ring-degree M`
- `N * M` must equal the number of participating GPUs
- `ALLOW_RESIZE_FOR_SP=1` only when the selected image size is not divisible by the sequence-parallel degree and the user accepts the resize

The wrapper can print the full command without executing it. Only run it on a host with enough GPUs and memory for the selected resolution.

## Output Handling

The sampler writes mp4 files under the chosen `--save-path`. The filename includes a timestamp and the seed. If you need a deterministic artifact name for downstream automation, wrap the save directory in a dedicated run folder.

## When to Revisit the Checklist

- The checkpoint tree is missing or incomplete.
- The prompt/image path is wrong.
- The user wants a different motion style or resolution.
- The host cannot fit the model at the requested resolution.
