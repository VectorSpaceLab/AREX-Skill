# Gradio Demo Behavior

This guide describes the self-contained Gradio launcher bundled with the generated skill. It preserves the important InfiniteYou demo controls and model-switching behavior while avoiding dependency on the original demo source file.

## Entry point

Use the bundled launcher:

```bash
python scripts/launch_infinite_you_gradio.py --check-only \
  --model-dir models/InfiniteYou \
  --base-model-path models/FLUX.1-dev

python scripts/launch_infinite_you_gradio.py \
  --model-dir models/InfiniteYou \
  --base-model-path models/FLUX.1-dev \
  --server-name localhost
```

The launcher uses the generated skill's `runtime/pipelines/` implementation by default. It accepts `--implementation-root` only when intentionally comparing a different compatible source tree.

## Download and exposure policy

- `--check-only` never downloads models or launches a server.
- Full launch defaults to local model paths and refuses missing/non-local model paths unless `--allow-downloads` is set.
- `--allow-downloads` may trigger upstream model loading/downloading behavior and should be used only after model-license/network approval.
- `--server-name` defaults to `localhost`.
- `--share` creates a public Gradio share link and should be used only with explicit approval.

## Model version defaults

| Symbol | Value | Meaning |
| --- | --- | --- |
| `sim_stage1` | exposed dropdown choice | Alternate model variant that favors higher identity similarity. |
| `aes_stage2` | default dropdown value | Default model variant for better alignment/aesthetics. |

## Cached pipeline behavior

The launcher keeps one cached pipeline and reuses it when the requested model version and LoRA toggles are unchanged.

- If the model version and LoRA state match the cached configuration, the existing pipeline is returned.
- If the model version changes, the old pipeline is deleted, Python garbage collection runs, and CUDA cache is cleared before a new pipeline is built.
- After the pipeline is available, the launcher clears previous `realism` and `anti_blur` adapters when the Diffusers object supports that operation, then loads only the selected LoRAs.
- Reusing the same model version with different LoRA toggles reuses the base pipeline and refreshes adapter state.

This cache policy reduces repeated reloads, but it does not remove the need for enough free VRAM when switching models.

## UI control map

| Control | Default | Effect |
| --- | --- | --- |
| Identity image | Required | Primary face input used for identity extraction. |
| Control image | Optional | If omitted, the pipeline uses a black control image. |
| Prompt | `Portrait, 4K, high quality, cinematic` | Text prompt for the generated scene. |
| Model version | `aes_stage2` | Chooses the default or higher-similarity model variant. |
| Seed | `0` | `0` means random seed generation. |
| Number of steps | `30` | Diffusion step count. |
| Width | `864` | Output width. |
| Height | `1152` | Output height. |
| Guidance scale | `3.5` | Diffusion guidance scale. |
| InfuseNet conditioning scale | `1.0` | Strength of the identity-conditioning signal. |
| InfuseNet guidance start | `0.0` | Start point for identity guidance. |
| InfuseNet guidance end | `1.0` | End point for identity guidance. |
| Realism LoRA | Off | Enables the optional realism adapter when present. |
| Anti-blur LoRA | Off | Enables the optional anti-blur adapter when present. |

## Differences from the source demo

- The generated launcher does not include repo-owned sample images or cache examples, so startup avoids automatic sample generation.
- The generated launcher is private by default (`localhost`) and uses explicit `--share` for public links.
- The generated launcher adds `--check-only` for no-side-effect validation before server launch.
- The generated launcher uses the bundled runtime, so it does not need the original checkout.

## Launch cautions

- Keep the default width and height when debugging startup or memory issues.
- Larger sizes can increase VRAM pressure sharply.
- If the model is being switched repeatedly, free other GPU jobs first.
- Do not expose the server externally unless you intentionally want network access and have chosen the bind and port accordingly.
- For tight VRAM, prefer the CLI wrapper with `--cpu-offload --quantize-8bit`; the demo launcher does not expose quantization/offload controls for pipeline construction.
