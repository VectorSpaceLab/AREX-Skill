# Server and Resource Troubleshooting

## Connection cannot be established

Checklist:

1. Normalize the URL:

   ```bash
   python sub-skills/server-resources/scripts/check_server_resources.py --parse-url localhost:8188
   ```

2. Confirm server mode: managed, external, or cloud.
3. For external mode, confirm ComfyUI is already running and reachable.
4. For managed mode, inspect `ServerState` before starting/installing.
5. For cloud mode, confirm access token and service availability without sending
   image/prompt data unless authorized.

## Server starts but plugin reports missing nodes

Likely cause: external/managed ComfyUI lacks required custom nodes or has
incompatible revisions.

Recovery:

- Inspect the required node list with the resource helper.
- Confirm the ComfyUI runtime, not just the plugin checkout, has the custom node
  packages installed.
- Restart ComfyUI after installing custom nodes.
- Re-run model/resource discovery before attempting generation.

## Missing checkpoint, inpaint, control, VAE, text encoder, upscaler, or LoRA

Recovery order:

1. Identify the selected `Arch` and workflow kind.
2. Determine required resource kind/control mode.
3. Check `ClientModels` discovery results or resource helper output.
4. Confirm file names and subfolders match ComfyUI discovery.
5. For inpaint, ensure the inpaint model lives in the expected model category,
   not only as a generic checkpoint.
6. For LoRA, verify prompt/style extraction with the document-image-state helper
   and server discovery with this sub-skill.

## Managed server install/download/upgrade fails

Common causes:

- Network failure, proxy/DNS problem, or remote host unavailable.
- Insufficient disk space for ComfyUI or model files.
- Existing partial install or interrupted download.
- Backend package mismatch for CUDA/ROCm/MPS/DirectML/XPU/CPU.
- Path length problems on Windows.
- Antivirus/permissions blocking extraction or execution.

Safe recovery:

- Do not delete model directories unless the user approves.
- Preserve logs and the server path.
- Use `parse_common_errors` output when available.
- Retry network downloads only after confirming connectivity and proxy.
- Prefer `verify`/`fix_models` for model-file problems over full reinstall.

## Port already in use

Recovery:

- Stop the conflicting ComfyUI/process, or choose a new port.
- For managed mode, check whether a previous Krita-managed server is still
  running.
- For external mode, update the plugin `server_url` to the actual port.

## Cloud errors

Common surfaces:

- Missing or expired access token.
- Insufficient funds.
- Service unavailable.
- Uploaded input/model rejected.
- User canceled or job timed out.

Recovery:

- Do not retry paid operations blindly.
- Report `ErrorKind.insufficient_funds` distinctly from server/plugin errors.
- Ask for authorization before sending any private image/prompt/workflow data to
  cloud services.

## Backend mismatch

Symptoms:

- CUDA selected on a non-NVIDIA machine.
- MPS selected off macOS.
- DirectML selected off Windows.
- ROCm/XPU package unavailable or unsupported.
- CPU backend works but generation is extremely slow.

Recovery:

- Use platform-supported backend list from `ServerBackend.supported()`.
- Treat CPU as a functional fallback only when the user accepts performance
  limits; do not use CPU checks to prove GPU behavior.
- If a workflow depends on an optional optimized node such as Nunchaku/GGUF,
  check both custom node availability and compatible model quantization.
