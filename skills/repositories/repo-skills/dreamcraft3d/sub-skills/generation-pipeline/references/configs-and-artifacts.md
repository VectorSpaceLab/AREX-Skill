# Configs and Artifacts

## Canonical DreamCraft3D configs

| Config | Stage | Geometry | Renderer | Prompt processor | Guidance | Trainer |
| --- | --- | --- | --- | --- | --- | --- |
| `configs/dreamcraft3d-coarse-nerf.yaml` | `coarse` | `implicit-volume` | `nerf-volume-renderer` | `deep-floyd-prompt-processor` | `deep-floyd-guidance` + `stable-zero123-guidance` | 5000 steps, `16-mixed` |
| `configs/dreamcraft3d-coarse-neus.yaml` | `coarse` | `implicit-sdf` | `neus-volume-renderer` | `deep-floyd-prompt-processor` | `deep-floyd-guidance` + `stable-zero123-guidance` | 5000 steps, `16-mixed` |
| `configs/dreamcraft3d-geometry.yaml` | `geometry` | `tetrahedra-sdf-grid` | `nvdiff-rasterizer` with `context_type: cuda` | `deep-floyd-prompt-processor` | `deep-floyd-guidance` + `stable-zero123-guidance` | 5000 steps, precision `32`, DDP unused-parameter strategy |
| `configs/dreamcraft3d-texture.yaml` | `texture` | fixed `tetrahedra-sdf-grid` | `nvdiff-rasterizer` with `context_type: cuda` | `stable-diffusion-prompt-processor` | `stable-diffusion-bsd-guidance` | 5000 steps, precision `32`, DDP unused-parameter strategy |

All four use `data_type: single-image-datamodule` and `system_type: dreamcraft3d-system`.

## Required overrides

The YAML files intentionally contain unresolved `???` values. Supply them at launch time:

| Stage | Required user/runtime values |
| --- | --- |
| coarse NeRF | `system.prompt_processor.prompt`, `data.image_path` |
| coarse NeuS | prompt, image path, `system.weights` from coarse NeRF checkpoint |
| geometry | prompt, image path, `system.geometry_convert_from` from coarse NeuS checkpoint |
| texture | prompt, image path, `system.geometry_convert_from` from geometry checkpoint |

If OmegaConf reports a missing mandatory value, check these overrides before debugging code.

## Key artifacts

| Artifact | Purpose |
| --- | --- |
| `_rgba.png`, `_depth.png`, `_normal.png` | Reference image, depth, and normal supervision loaded by `single-image-datamodule`. |
| `load/zero123/stable_zero123.ckpt` or equivalent stable Zero123 checkpoint | View-conditioned 3D guidance for coarse/geometry stages. The config uses the underscore filename. |
| `load/zero123/sd-objaverse-finetune-c_concat-256.yaml` | Stable Zero123 architecture/config file. |
| `load/tets/128_tets.npz` | DMTet grid used by geometry and texture stages at `isosurface_resolution: 128`. |
| DeepFloyd IF cache | Coarse/geometry prompt processor and 2D diffusion guidance. |
| Stable Diffusion 2.1 base cache | Texture stage BSD guidance and prompt processor. |
| Optional LoRA output folder | Passed through `system.guidance.lora_weights_path` when using personalized texture boosting. |

## Registry names to recognize

DreamCraft3D inherits a threestudio registry pattern. Important registered names include:

- `dreamcraft3d-system`, `zero123-system`
- `single-image-datamodule`, `random-camera-datamodule`
- `implicit-volume`, `implicit-sdf`, `tetrahedra-sdf-grid`
- `nerf-volume-renderer`, `neus-volume-renderer`, `nvdiff-rasterizer`
- `deep-floyd-guidance`, `stable-zero123-guidance`, `stable-diffusion-bsd-guidance`
- `deep-floyd-prompt-processor`, `stable-diffusion-prompt-processor`
- `mesh-exporter`

Use these names when matching config values to source behavior or error messages.

## Memory and resolution controls

The default README path targets large GPUs; the project notes A100 40GB defaults. To reduce memory use, lower resolution-related overrides, for example:

```bash
data.height=128 data.width=128 data.random_camera.height=128 data.random_camera.width=128
```

Use lower resolution for diagnosis or small-memory experimentation, but do not treat it as quality-equivalent to paper/default settings.

## Output naming

The config `tag` uses the prompt with spaces replaced by underscores. Commands and scripts should quote the prompt and avoid assuming the shell-safe tag is identical to the original prompt.
