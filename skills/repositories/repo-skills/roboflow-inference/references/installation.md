# Installation

This page gives the minimal install map for the public Roboflow Inference
surfaces.
Use it when a command, stream, or model load fails because the package is not
available.

## Package map

| Surface | Minimal package / extra | Notes |
| --- | --- | --- |
| CLI and server family | `inference-cli` | Use for `inference`, `server`, `infer`, `benchmark`, `cloud`, `rf-cloud`, and enterprise command families. |
| Local workflow execution | `inference` | Needed when workflow commands execute through the local `inference` package. |
| SDK and HTTP client | `inference-sdk` | Use for `InferenceHTTPClient` and workflow/pipeline HTTP calls. |
| SDK WebRTC streaming | `inference-sdk[webrtc]` | Needed when `aiortc` / `av` WebRTC support is missing. |
| Model runtime | `inference-models` | Use for `AutoModel`, backend negotiation, and package loading. |
| Cloud deploy support | `inference[cloud-deploy]` | Needed for the `cloud` command family and SkyPilot integration. |
| Cloud storage support | `inference[cloud-storage]` | Needed for cloud-storage-backed data staging paths. |

## Practical notes

- The local workflow/video commands expect the `inference` package to be
  importable in the runtime environment that executes them.
- The CLI family depends on Docker for server lifecycle commands and the
  enterprise compiler container mode.
- The SDK base install is separate from WebRTC support. If streaming helpers fail
  with missing `aiortc` or `av`, install the WebRTC extra.
- The model-runtime package has its own backend extras and environment matrix.
  Read [`../sub-skills/model-runtime/references/backends.md`](../sub-skills/model-runtime/references/backends.md)
  for the backend choice and GPU/CPU extras.

## Quick install examples

```bash
pip install inference-cli
pip install inference-sdk
pip install inference-models
```

For WebRTC streaming:

```bash
pip install "inference-sdk[webrtc]"
```

For cloud deploy:

```bash
pip install "inference[cloud-deploy]"
```

For cloud storage / staging:

```bash
pip install "inference[cloud-storage]"
```

## When the package is still missing

If the command still reports a missing import after installation, open the
matching troubleshooting page:

- CLI/server/cloud/rf-cloud/enterprise issues → `cli-operations`
- Workflow command issues → `workflow-processing`
- WebRTC or HTTP client issues → `sdk-webrtc`
- Backend / package negotiation / local package issues → `model-runtime`
