---
name: omnilive
description: "Guide InternLM-XComposer2.5-OmniLive audio, video-memory, runnable
  service entrypoints, and benchmark workflows with explicit execution gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OmniLive Sub-skill

Use this sub-skill when the task is specifically about InternLM-XComposer2.5-OmniLive (IXC2.5-OL): audio understanding, OmniLive model directory layout, image/VLM smoke planning with the OmniLive `base` component, long/streaming video QA with `memory`, online SRS/FastAPI/Gradio deployments, or OmniLive audio/video benchmarks.

For generic InternLM-XComposer 2.5 image/video/chat/composition inference that does not depend on OmniLive audio, `memory`, SRS, or OmniLive checkpoints, route through the sibling `model-inference` sub-skill instead.

## Operating checklist

1. Identify the requested OmniLive workflow:
   - audio ASR/classification;
   - base VLM image/video sanity check;
   - memory-backed video QA;
   - SRS + JavaScript frontend + FastAPI backend service;
   - Gradio frontend + three FastAPI backend processes;
   - audio/video/streaming benchmark planning.
2. Validate the local model root before writing commands. A complete downloaded OmniLive root is expected to expose component directories named `audio/`, `base/`, `adapter/`, `memory/`, and `merge_lora/`. The `merge_lora/` component is an output of merging `base/` with `adapter/`; memory video QA and online backends should not be planned against only `base/` + `adapter/`.
3. Use the bundled helper `scripts/check_omnilive_layout.py` to inspect model layout safely. It never imports torch, starts services, downloads models, or reads an original source checkout.
4. Use the bundled helper `scripts/render_service_plan.py` to print a deployment plan for SRS or Gradio services. It renders commands and configuration edits but does not start listeners.
5. For approved local execution, use the repaired self-contained entrypoint bundles rather than source checkout files:
   - `entrypoints/omnilive-examples/` for audio ASR/classification, base VLM image QA, `base/` + `adapter/` LoRA merge, and memory-backed video QA;
   - `entrypoints/omnilive-gradio/` for the Gradio frontend plus FastAPI backend trio;
   - `entrypoints/omnilive-srs/` for the SRS Docker launcher, JavaScript frontend, and FastAPI backend package.
6. Load the nearest detailed reference before producing a plan:
   - `references/workflows.md` for audio/base/memory examples and model arguments;
   - `references/service-deployment.md` for SRS, FastAPI, frontend, LAN IP, remote backend, VAD, and Gradio flags;
   - `references/benchmark-workflows.md` for audio/video benchmark layouts and launcher patterns;
   - `references/troubleshooting.md` for dependency, model layout, network, VAD, and threshold failures.

## Bundled scripts and entrypoints

Safe planners/checkers:

- `scripts/check_omnilive_layout.py`
- `scripts/render_service_plan.py`

Runnable self-contained entrypoints:

- `entrypoints/omnilive-examples/infer_audio.py`
- `entrypoints/omnilive-examples/infer_llm_base.py`
- `entrypoints/omnilive-examples/merge_lora.py`
- `entrypoints/omnilive-examples/infer_llm_with_memory.py`
- `entrypoints/omnilive-gradio/backend.sh`
- `entrypoints/omnilive-gradio/backend_vs.py`
- `entrypoints/omnilive-gradio/backend_llm.py`
- `entrypoints/omnilive-gradio/backend.py`
- `entrypoints/omnilive-gradio/frontend.py`
- `entrypoints/omnilive-gradio/launch_frontend.sh`
- `entrypoints/omnilive-srs/run_srs_docker.sh`
- `entrypoints/omnilive-srs/run_backend.sh`
- `entrypoints/omnilive-srs/run_frontend_dev.sh`

Read the bundle `README.md` files before execution. These entrypoints are real CUDA/model/service workloads; keep validation and approval gates explicit.

## Boundaries

- Include OmniLive-specific audio, memory/video, online-demo, and benchmark workflows.
- Do not describe third-party Melo TTS internals beyond dependency and failure notes.
- Do not start SRS, FastAPI, Gradio, Node, torch, Swift, LMDeploy, or benchmark jobs during planning/validation unless the user explicitly asks from a Researcher session with the required environment.
- Do not assume the original repository checkout is available. Provide self-contained plans and ask the user for their model root, service app location, dataset root, and host/network details when execution paths are needed.
