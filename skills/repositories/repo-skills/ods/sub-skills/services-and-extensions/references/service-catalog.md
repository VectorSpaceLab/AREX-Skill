# Service Catalog

This reference summarizes the current bundled runtime service catalog and the
installable library catalog for ODS extensions.

## Reading the port column

- `A→B` means the manifest's internal `service.port` is `A` and the public or
  default port is `B`.
- `A (internal-only)` means the service has no published public port.
- `host-network` means Docker host networking is used, so there is no
  Docker-mapped port.

## Bundled runtime catalog

Snapshot: 27 services, 7 core, 5 recommended, 15 optional.
Type mix: 26 docker, 1 host-systemd.
Backend mix: 22 all, 5 amd, 5 nvidia.

| ID                         | Category    | Port                  | GPU backends | Type         |
|----------------------------|-------------|-----------------------|--------------|--------------|
| ape                        | optional    | 7890                  | all          | docker       |
| brave-search               | optional    | 8585                  | all          | docker       |
| comfyui                    | optional    | 8188                  | amd,nvidia   | docker       |
| dashboard                  | core        | 3001                  | amd,nvidia   | docker       |
| dashboard-api              | core        | 3002                  | amd,nvidia   | docker       |
| embeddings                 | optional    | 80→8090               | all          | docker       |
| hermes                     | recommended | 9119 (internal-only)  | all          | docker       |
| hermes-proxy               | recommended | 9120                  | all          | docker       |
| langfuse                   | optional    | 3000→3006             | all          | docker       |
| litellm                    | recommended | 4000                  | all          | docker       |
| llama-server               | core        | 8080→11434            | amd,nvidia   | docker       |
| model-router               | core        | 9099                  | all          | docker       |
| n8n                        | optional    | 5678                  | all          | docker       |
| ods-proxy                  | optional    | 80                    | all          | docker       |
| open-webui                 | core        | 8080→3000             | amd,nvidia   | docker       |
| openclaw                   | optional    | 18789→7860            | all          | docker       |
| opencode                   | optional    | 3003                  | all          | host-systemd |
| perplexica                 | optional    | 3000→3004             | all          | docker       |
| privacy-shield             | optional    | 8085                  | all          | docker       |
| qdrant                     | optional    | 6333                  | all          | docker       |
| remote-provider-egress     | core        | 8091 (internal-only)  | all          | docker       |
| remote-provider-ssh-tunnel | core        | 18090 (internal-only) | all          | docker       |
| searxng                    | recommended | 8080→8888             | all          | docker       |
| tailscale                  | optional    | host-network          | all          | docker       |
| token-spy                  | recommended | 8080→3005             | all          | docker       |
| tts                        | optional    | 8880                  | all          | docker       |
| whisper                    | optional    | 8000→9000             | all          | docker       |

Activation state is snapshot-specific. Use `scripts/extension_manifest_summary.py --root <catalog-root>` when you need enabled, disabled, core-only, or host-network status.

## Installable library catalog

Snapshot: 33 services, 2 recommended, 31 optional.
Backend coverage: 24 nvidia, 19 amd, 9 all, 8 apple.

The library uses the same manifest contract as the bundled runtime services.
Some entries ship with `compose.yaml.disabled` so they stay opt-in until
explicitly enabled.

### Category groups

- LLM inference & chat: aider, anythingllm, localai, text-generation-webui,
  jan, librechat, ollama
- Voice & audio: bark, xtts, piper-audio, rvc, audiocraft
- Image generation: comfyui, fooocus, invokeai, forge
- AI development & agents: continue, crewai, gaia, open-interpreter, jupyter
- Vector databases: chromadb, milvus, weaviate
- Workflow automation: flowise, langflow, dify
- Self-hosted apps: immich, paperless-ngx, frigate, gitea, baserow,
  sillytavern
- Data & ML: label-studio

### Library inventory by category

| Category | Service ids |
|---|---|
| optional | aider, anythingllm, audiocraft, bark, baserow, chromadb, continue, crewai, dify, flowise, fooocus, forge, frigate, gaia, gitea, immich, invokeai, jan, jupyter, label-studio, langflow, librechat, localai, ollama, open-interpreter, paperless-ngx, piper-audio, rvc, sillytavern, text-generation-webui, weaviate |
| recommended | milvus, xtts |

## How to use this snapshot

- Use `scripts/extension_manifest_summary.py --root <catalog-root>` to refresh
  the same kind of inventory on another checkout.
- Treat bundled runtime services as the always-available stack surface.
- Treat library services as installable catalog entries that may still be
  disabled by default.
- Use the service manifest category plus port and backend data before deciding
  whether an extension should be built into the base stack, shipped as a
  recommended service, or left optional.
