# Model Families

This table is a compact reminder of the major `model_cls` families and the task shapes they commonly support.

| Family | Common tasks | Notes |
| --- | --- | --- |
| Wan 2.1 / 2.2 | `t2v`, `i2v`, `i2i`, `vace`, `animate`, `s2v`, `rs2v`, `t2av`, `i2av`, `l2av`, `fl2av`, `ref2av` | The broadest family. Often uses family-specific offload and parallel settings. Wan 2.2 may split low-noise and high-noise branches. |
| Qwen Image / Qwen Image Edit | `t2i`, `i2i` | Uses prompt templates and image-conditioning fields that differ from the video families. |
| HunyuanVideo-1.5 | `t2v`, `i2v` | Often points to a transformer subdirectory and may use parallel/offload tuning. |
| Hunyuan Image 3 | `t2i`, `ti2t`, `ti2i` | Uses model-specific text / image encoder and decoder config normalization. |
| LTX-2 / LTX-2.5 | `t2v`, `i2v`, `ltx2_s2v`, `s2v` | LTX-2.5 may infer several component checkpoints from the model root and may auto-derive the final video length. |
| MiniMax-H3 | `t2av`, `i2av`, `l2av`, `fl2av`, `ref2av` | Requires audio-aware inputs and has its own FPS / flow-shift assumptions. |
| WorldMirror | `recon`, `sr` | Uses input directories, optional camera/depth priors, and an optional rendered fly-through. |
| WorldPlay | `i2v` with action / pose conditioning | The action checkpoint and pose string matter more than a generic prompt-only run. |
| SeedVR2 | `sr` | Super-resolution flow, often with image or video input and an output scale ratio. |
| Bagel / SenseNova-Vision / ERNIE / Z-Image / LongCat / Flux2 / Neopp / Motus / LingBot / FastWAM / InfiniteTalk / DreamZero / Cosmos3 / Hunyuan3D | family-specific tasks | These families are supported by the inference stack, but they each have their own special path or input conventions. |

## Special path reminders

- `sensenova_vision` only makes sense with `omni_vision_task`.
- `wan22_animate2_distilled` expects a non-negative seed.
- `worldmirror` uses a `subfolder` override when the weights live below the model root.
- `minimax_h3` expects audio/video request fields and a family-appropriate transformer subfolder.
- `ltx2_5` may resolve component checkpoints from the root tree and then merge metadata from the checkpoint file.

## Use this table as a routing aid

If the user only says "Wan", "Qwen", "LTX", "WorldMirror", or "MiniMax-H3", use this table to decide the family-specific workflow first, then read `workflows.md` for the common configuration flow.
