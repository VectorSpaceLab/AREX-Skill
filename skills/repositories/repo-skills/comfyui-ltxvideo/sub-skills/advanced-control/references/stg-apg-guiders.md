# STG and APG Guiders

Related routes: [root backend requirements](../../../references/model-and-backend-requirements.md) · [core-generation](../../core-generation/SKILL.md) · [prompt-conditioning](../../prompt-conditioning/SKILL.md)

Use this reference when the user wants to change how the model is guided during denoising rather than how the graph is assembled.

## Core distinction

- `LTXVApplySTG` only marks transformer blocks to be skipped. It does **not** build a guider by itself.
- `STGGuider` is the simple constant-parameter STG guider.
- `STGGuiderAdvanced` is the sigma-aware STG guider with optional APG stacking.
- `APGGuider` is APG alone.
- `STGAdvancedPresets` only selects a preset name; the actual schedule is summarized in the preset catalog below.

## APG-specific controls

- `APGGuider` exposes `cfg_scale`, `eta`, `norm_threshold`, and `momentum_coefficient`.
- Use APG alone when you want projected guidance without STG block skipping.
- Keep the APG settings conservative first; `eta` and `norm_threshold` are the knobs that change the projection most directly.

## How the knobs differ

| Node or field | What it controls | Important caveat |
| --- | --- | --- |
| `block_indices` on `LTXVApplySTG` | Comma-separated transformer blocks to wrap | This is block skipping, not sigma scheduling. |
| `cfg` on `STGGuider` | Standard CFG strength | Use this only when one constant CFG is enough. |
| `stg` on `STGGuider` | STG strength | Higher values increase the effect of the skip/perturbation path. |
| `rescale` on `STGGuider` | Blends the rescaled prediction back toward the original variance | `0` disables the blend, `1` fully applies it. |
| `skip_steps_sigma_threshold` | Zeroes steps whose sigma is above the threshold | The comparison is against sigma, not step index. |
| `cfg_star_rescale` | Rescales the negative prediction by its dot product with the positive path | This is a CFG-Zero* style correction, not a generic CFG toggle. |
| `stg_layers_indices` | Per-sigma lists of blocks to skip | Each sigma slot must have a matching list entry. |
| `apply_apg` | Adds APG after the STG result | Keep APG off unless the user explicitly wants it. |

## Preset catalog

`Custom` means manual lists are used. Any non-custom preset overrides the manual fields.

- `13b Dynamic`
  - sigmas: `1.0, 0.9933, 0.9850, 0.9767, 0.9008, 0.6180`
  - cfg: `1, 6, 8, 6, 1, 1`
  - stg scale: `0, 4, 4, 4, 2, 1`
  - rescale: `1, 0.5, 0.5, 1, 1, 1`
  - layer lists: `[[11, 25, 35, 39], [22, 35, 39], [28], [28], [28], [28]]`
  - use when the user wants a more dynamic 13B control schedule.

- `13b Balanced`
  - sigmas: `1.0, 0.9933, 0.9850, 0.9767, 0.9008, 0.6180`
  - cfg: `1, 6, 8, 6, 1, 1`
  - stg scale: `0, 4, 4, 4, 2, 1`
  - rescale: `1, 0.5, 0.5, 1, 1, 1`
  - layer lists: `[[12], [12], [5], [5], [28], [29]]`
  - this is the safest default preset when the user is unsure.

- `13b Upscale`
  - sigmas: `1.0, 0.9933, 0.9850, 0.9767, 0.9008, 0.6180`
  - cfg: `1, 1, 1, 1, 1, 1`
  - stg scale: `1, 1, 1, 1, 1, 1`
  - rescale: `1, 1, 1, 1, 1, 1`
  - layer lists: `[[42], [42], [42], [42], [42], [42]]`
  - use when the user is looking for an upscale-style pass rather than strong guidance.

- `13b Distilled`
  - sigmas: `1.0`
  - cfg: `1`
  - stg scale: `0`
  - rescale: `1`
  - layer lists: `[[25]]`
  - use for the shortest distilled path.

- `2b`
  - sigmas: `1.0, 0.9933, 0.9850, 0.9767, 0.9008, 0.6180`
  - cfg: `4, 4, 4, 4, 1, 1`
  - stg scale: `2, 2, 2, 2, 1, 0`
  - rescale: `1, 1, 1, 1, 1, 1`
  - layer lists: `[[14], [14], [14], [14], [14], [14]]`
  - use when the smaller model branch needs a stronger CFG-backed schedule.

## Reasoning rules

1. If the task only needs a single constant guidance setting, use `STGGuider` or `APGGuider` rather than the advanced schedule.
2. If the user asks for a schedule that changes with denoising progress, use `STGGuiderAdvanced`.
3. If the user says “use the preset”, treat the preset as authoritative and ignore the manual lists.
4. If the user names block indices but not sigma scheduling, `LTXVApplySTG` is the lightest answer.
5. If the task is really about generic `cfg`/`rescale` wiring, route back to [prompt-conditioning](../../prompt-conditioning/SKILL.md) unless the user explicitly wants expert STG/APG behavior.

## Typical failure modes

- `Preset X not found in the presets list.` means the preset string does not match a bundled preset.
- A manual schedule with unequal list lengths will misalign sigma slots and should be rewritten.
- If the chosen blocks have no visible effect, the model family may not expose the same transformer block layout.
- `stg_layers_indices` and the `block_indices` helper are different layers of control: one chooses blocks to wrap, the other chooses the attention sites inside those blocks.
