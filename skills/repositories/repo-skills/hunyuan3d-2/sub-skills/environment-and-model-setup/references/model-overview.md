# Model Overview and Cache Planning

## VRAM guidance

Repository docs state approximate memory needs:

- Shape generation: about 6 GB VRAM.
- Shape + texture generation: README states about 16 GB total; docs/modelzoo states about 24.5 GB total. Treat the larger value as safer for production planning.

Actual memory depends on model variant, `octree_resolution`, `num_chunks`, mesh face count, texture stage, and concurrency.

## Shape model zoo

| Series | Model repo | Subfolders | Use |
| --- | --- | --- | --- |
| Hunyuan3D-2 | `tencent/Hunyuan3D-2` | `hunyuan3d-dit-v2-0`, `hunyuan3d-dit-v2-0-fast`, `hunyuan3d-dit-v2-0-turbo` | Base single-view image-to-shape. |
| Hunyuan3D-2mini | `tencent/Hunyuan3D-2mini` | `hunyuan3d-dit-v2-mini`, `hunyuan3d-dit-v2-mini-fast`, `hunyuan3d-dit-v2-mini-turbo` | Smaller/faster 0.6B shape model. |
| Hunyuan3D-2mv | `tencent/Hunyuan3D-2mv` | `hunyuan3d-dit-v2-mv`, `hunyuan3d-dit-v2-mv-fast`, `hunyuan3d-dit-v2-mv-turbo` | Multiview image-to-shape. |
| Hunyuan3D-2.1 | `tencent/Hunyuan3D-2.1` | `hunyuan3d-dit-v2-1` | Newer 3.0B model mentioned in README; verify package compatibility and task need before using. |

## Texture model zoo

| Model repo | Subfolder | Use |
| --- | --- | --- |
| `tencent/Hunyuan3D-2` | `hunyuan3d-paint-v2-0` | Standard Hunyuan3D-Paint texture generation. |
| `tencent/Hunyuan3D-2` | `hunyuan3d-paint-v2-0-turbo` | Distilled/turbo texture generation; current default in `Hunyuan3DPaintPipeline.from_pretrained`. |
| `tencent/Hunyuan3D-2` | `hunyuan3d-delight-v2-0` | Required by paint pipeline for delighting input images. |

## VAE subfolders used by FlashVDM and VAE demos

- `tencent/Hunyuan3D-2/hunyuan3d-vae-v2-0`
- `tencent/Hunyuan3D-2/hunyuan3d-vae-v2-0-turbo`
- `tencent/Hunyuan3D-2mini/hunyuan3d-vae-v2-mini`
- `tencent/Hunyuan3D-2mini/hunyuan3d-vae-v2-mini-turbo`
- `*-withencoder` variants for VAE encode/decode demos.

`pipeline.enable_flashvdm()` can replace the VAE based on the `model_path` repo name. Ensure these VAE subfolders are cached or downloadable when using FlashVDM.

## Cache behavior

Shape loading checks:

```text
${HY3DGEN_MODELS:-~/.cache/hy3dgen}/<model_path>/<subfolder>
```

If the subfolder does not exist, it calls Hugging Face `snapshot_download` with an allow-pattern for that subfolder.

Texture loading similarly checks a local model directory under `${HY3DGEN_MODELS:-~/.cache/hy3dgen}` and needs both delight and paint subfolders. If absent, it downloads allowed subfolders from the model repo.

Operational recommendations:

1. Set `HY3DGEN_MODELS` to a shared cache location for repeatable production runs.
2. Pre-download exact subfolders needed for offline/air-gapped runs.
3. Record model repo ids and subfolders in experiment outputs so future agents can reproduce the same variant.
4. Do not use README marketing links as proof that weights are locally available.

## Selecting a model quickly

| Task | Preferred choice |
| --- | --- |
| Fast single-image draft | `tencent/Hunyuan3D-2` + `hunyuan3d-dit-v2-0-turbo` + FlashVDM, or mini turbo if quality tradeoff is acceptable. |
| Higher-quality single-image shape | Base `hunyuan3d-dit-v2-0` with more steps and higher octree resolution. |
| Multiple view images | `tencent/Hunyuan3D-2mv` with mv subfolder matching desired speed. |
| Texture existing mesh | `tencent/Hunyuan3D-2` + `hunyuan3d-paint-v2-0-turbo` first, standard paint if turbo artifacts matter. |
| Low-VRAM service demo | Mini/turbo shape, lower octree resolution, texture disabled or low-vram Gradio mode. |
