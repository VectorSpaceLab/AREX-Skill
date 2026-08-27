# Export and static inference

This reference covers the bundled export wrapper, the static artifact layout it produces, and the generic Paddle Inference Python planner used by this sub-skill.

## Export flow

1. Load the training config.
2. Build the model from `cfg.model`.
3. Load the checkpoint into the model nets.
4. Convert the configured nets to static graphs.
5. Save `.pdmodel` and `.pdiparams` files under the chosen output prefix.
6. Optionally add Serving artifacts when `--export_serving_model` is enabled.

The bundled wrapper follows the repo's export semantics but adds two safety guards:
- it validates the `inputs_size` string format before export,
- it avoids a shared `model_name` prefix for multi-net base exports so one branch does not overwrite another.

## `inputs_size` string rules

`--inputs_size` is a semicolon-separated list of shapes. Each shape is a comma-separated list of integers.

Examples:

| Shape string | Meaning |
| --- | --- |
| `1,3,128,128` | one 4D tensor |
| `-1,3,-1,-1` | one dynamic 4D tensor |
| `1,3,256,256;1,3,256,256` | two same-shape inputs |
| `1,1,512;1,1` | style vector plus truncation scalar |
| `1,3,256,256;1,3,256,256;1,10,2;1,10,2,2` | multi-input FOM export |

Rules:
- Keep the order aligned with the export config or the model-specific export method.
- Use quotes around the whole string when semicolons are present.
- Negative dimensions are only meaningful where the runtime path can accept dynamic axes.
- The number of provided shapes must match the total exported input count when the export config is a normal named-net list.

## Export config semantics

When `cfg.export_model` is a normal list of dictionaries, each item describes one exported network.

Common keys:
- `name`: the key in `model.nets`.
- `inputs_num`: how many input tensors that net consumes.

Examples:

| Model family | Export key(s) | Notes |
| --- | --- | --- |
| CycleGAN | `netG_A`, `netG_B` | multi-net base export; keep distinct prefixes |
| Pix2Pix | `netG` | single exported generator |
| BasicVSR / MSVSR / EDVR / ESRGAN / AOTGAN / NAFNet / SwinIR / InvDN / GFPGAN | model-specific generator key | usually one exported net |
| StyleGANv2 | `gen` | custom export method, two inputs |
| Wav2Lip | `netG` | checkpoint is loaded as one net |
| FirstOrder/FOM | custom path | ignores the usual named-net export loop and writes `fom_dy2st/` |

### Checkpoint key handling

- Most training checkpoints are dicts keyed by net name.
- Multi-net exports should load matching keys from the checkpoint dict.
- Wav2Lip uses a direct `netG` load path.
- If a checkpoint key is missing, that usually means the wrong checkpoint or a stale prefix, not a recoverable export issue.

## Static artifact naming

The default static prefix becomes `<classlower>_<netname>` when the model uses the generic export loop.

Generated files usually follow this pattern:
- `PREFIX.pdmodel`
- `PREFIX.pdiparams`
- `PREFIX.pdiparams.info`

Serving export adds:
- `PREFIX/serving_client/`
- `PREFIX/serving_server/`

If a generic multi-net export is forced through a shared prefix, one branch can overwrite the other. Leave the prefix unset in that case and let the per-net default names stand.

FirstOrder/FOM is special:
- `fom_dy2st/kp_detector.pdmodel`
- `fom_dy2st/kp_detector.pdiparams`
- `fom_dy2st/generator.pdmodel`
- `fom_dy2st/generator.pdiparams`

## Checking exported artifacts

Use the bundled checker on either a prefix or an output directory:

```bash
python scripts/check_exported_model.py ./export_dir/inference
python scripts/check_exported_model.py ./export_dir --expect-prefix cycleganmodel_netG_A --expect-prefix cycleganmodel_netG_B
python scripts/check_exported_model.py ./export_dir/fom_dy2st
```

The checker verifies:
- exported `.pdmodel` / `.pdiparams` pairs exist,
- optional `.pdiparams.info` files are present when expected,
- nested exports such as `fom_dy2st/` are discoverable.

## Paddle Inference Python planner

The generic static inference helper uses these core flags:

| Flag | Purpose | Notes |
| --- | --- | --- |
| `--model_path` | exported model prefix | pass the prefix without `.pdmodel` / `.pdiparams` |
| `--config-file` | config used for test data and metrics | should match the model family |
| `--model_type` | route to the correct inference branch | must match the exported family |
| `--device` | `cpu`, `gpu`, `xpu`, or `npu` | `gpu` is the common deployment path here |
| `--run_mode` | `fluid`, `trt_fp32`, or `trt_fp16` | TRT modes require a TRT-enabled Paddle build |
| `--min_subgraph_size` | minimum TensorRT subgraph size | larger values reduce TRT coverage |
| `--use_dynamic_shape` | enable TRT dynamic shape hints | only useful when the feed names and shapes line up |
| `--trt_min_shape` / `--trt_max_shape` / `--trt_opt_shape` | dynamic-shape bounds | set them per input family |
| `--batch_size` | TRT batch bound | should match the deployment plan |

Model-type planning notes:
- `pix2pix`, `cyclegan`, `gfpgan`, `aotgan`, `nafnet`, `invdn` are image-oriented branches.
- `esrgan`, `edvr`, `basicvsr`, `msvsr`, `swinir` are restoration / sequence branches.
- `stylegan2` uses latent noise plus truncation.
- `wav2lip` uses audio mel and face tensors.
- `cyclegan` also pulls in optional benchmark logging.

### TensorRT planning notes

- `run_mode=trt_fp32` or `trt_fp16` only makes sense when the installed Paddle wheel/lib was built with TensorRT support.
- If the wheel says `tensorrt_op` is missing, stay on `fluid` or another non-TRT path.
- The generic dynamic-shape branch in the helper uses a common `image` feed key; verify feed names before depending on it for multi-input models.
- Increase `min_subgraph_size` when TensorRT reports small unsupported subgraphs or dynamic-shape warnings.
- If the runtime says `Slice on batch axis is not supported`, use dynamic shapes or fall back to `fluid`.

## FirstOrder / FOM static export

FirstOrder motion export is not handled by the generic multi-net loop.
It writes a `fom_dy2st/` directory with two static prefixes:
- `kp_detector`
- `generator`

That export is the handoff point for the dedicated FOM inference path and for the mobile deployment notes in `references/deployment-targets.md`.
