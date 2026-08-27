# Resources and Models Reference

`ai_diffusion.backend.resources` is the central catalog for supported model
architectures, required/optional ComfyUI custom nodes, model files, workloads,
resource IDs, and verification status.

Baseline catalog version for this skill: `1.52.0`.

## Required custom nodes

The catalog requires these custom node packages for full external/managed
ComfyUI compatibility:

| Node package | Folder | Purpose |
| --- | --- | --- |
| ControlNet Preprocessors | `comfyui_controlnet_aux` | preprocessors such as inpaint/depth helpers. |
| IP-Adapter | `ComfyUI_IPAdapter_plus` | IP-Adapter model loading/application. |
| External Tooling Nodes | `comfyui-tooling-nodes` | ETN cache/image/translation/tooling nodes used by plugin workflows and custom graphs. |
| Inpaint Nodes | `comfyui-inpaint-nodes` | inpaint load/shrink/stabilize/color-match helpers. |

Optional custom nodes include GGUF and Nunchaku support. Do not require optional
nodes unless the selected model/quantization path needs them.

## Architectures

`Arch` includes Stable Diffusion, SDXL-like, Flux-like, Qwen-like, edit, and
newer families. Values in this snapshot:

```text
sd15, sdxl, sd3, flux, flux_k, flux2_4b, flux2_9b, illu, illu_v,
chroma, qwen, qwen_e, qwen_e_p, qwen_l, anima, zimage, ernie, krea2,
auto, all
```

Feature support varies by architecture:

- `supports_regions`: region attention is only available for selected families.
- `supports_lcm`, `supports_clip_skip`, `supports_attention_guidance`, and
  `supports_cfg` are architecture-dependent.
- Edit models (`flux_k`, Qwen edit/layered families, Flux 2 variants) change
  prompt/reference behavior.
- Control and inpaint model selection must match architecture; a checkpoint name
  alone is not enough if server discovery reports detailed metadata.

## Resource identifiers and model kinds

`ResourceKind` covers model classes such as checkpoints, controlnet, clip
vision, IP adapter, LoRA, upscaler, inpaint, text encoders, VAE, preprocessor,
node, and workload-related resources. `ResourceId` combines kind, architecture,
identifier, and optional control mode.

When troubleshooting missing resources:

1. Determine the selected checkpoint architecture.
2. Determine whether the workflow needs control, inpaint, upscaler, LoRA,
   text-encoder, VAE, or optional quantized resources.
3. Compare the required resource ID/kind against discovered `ClientModels`.
4. Check whether missing resources are required, recommended, optional, or
   alternatives.

## Read-only resource inspection

Use:

```bash
python sub-skills/server-resources/scripts/check_server_resources.py --summary
```

This prints catalog version, ComfyUI version baseline, required/optional custom
nodes, architecture values, and compact resource counts. It does not contact a
server.

## External ComfyUI setup guidance

For external servers, the plugin does not install dependencies. The user must
ensure:

- ComfyUI is reachable at the configured URL.
- Required custom nodes are installed and importable in the ComfyUI runtime.
- Model files are located where ComfyUI can discover them, including paths from
  ComfyUI's own extra model path configuration.
- The server exposes checkpoints, LoRAs, control models, VAEs, upscalers, and
  text encoders through discovery compatible with the plugin.
- The plugin's setting to refuse connection when resources are missing is
  considered when missing optional resources are acceptable.

## Managed server resource guidance

Managed install/download/verify/fix operations use this catalog to decide which
ComfyUI revision, custom node revisions, and model packages are expected. These
operations can download large files and mutate the server directory. Keep them
out of default verification and only run after user authorization.

## Missing LoRA diagnosis

LoRA failures often cross prompt and server state:

- Prompt tags like `<lora:name:0.7>` are parsed by prompt preparation.
- Style JSON can add LoRAs independently of prompt tags.
- The final `CheckpointInput.loras` must reference model names known to the
  client/server or remote file library.
- Case, subfolder, file extension, and metadata aliases can affect matching.

Use `document-image-state` for tag extraction and this sub-skill for server
model availability.
