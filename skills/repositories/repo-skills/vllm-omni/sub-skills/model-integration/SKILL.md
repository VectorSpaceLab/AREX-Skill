---
name: model-integration
description: "Extend vLLM-Omni with custom diffusion pipelines, model
  registrations, TTS adapter contracts, and focused maintainer tests without
  running broad model suites by default."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model integration

Use this sub-skill when the user is editing or extending vLLM-Omni itself: adding a model family, wiring a custom diffusion pipeline, updating a TTS adapter, or choosing focused maintainer tests before a larger GPU run.

## Route here for

- Creating a custom diffusion pipeline using `diffusion_load_format`, `custom_pipeline_args`, `WorkerWrapperBase`, or `CustomPipelineWorkerExtension`.
- Adding or updating an omni AR, diffusion, TTS, action/world-model, or model-extra integration.
- Registering a `model_type`, pipeline topology, default deploy config, endpoint restrictions, or serving adapter.
- Reviewing OpenAI TTS adapter shape and optional dependency behavior.
- Choosing focused CPU parser/config/unit tests before expensive GPU/full-model examples.

## Route elsewhere

- Local Python inference with existing models: use the sibling offline-inference sub-skill.
- HTTP serving payloads and server launch commands: use the sibling online-serving sub-skill.
- Deploy YAML overlays, connectors, placement, or memory planning: use the sibling stage-configuration sub-skill.
- Choosing an already supported model/recipe/backend: use the sibling model-recipes sub-skill.

## Start here

1. Read [custom-pipeline-and-model-registration.md](references/custom-pipeline-and-model-registration.md) for extension surfaces and registration flow.
2. Read [maintainer-workflows.md](references/maintainer-workflows.md) before selecting tests or editing broad model code.
3. For TTS adapter edits, run or adapt the safe static checker:

   ```bash
   python scripts/check_tts_adapter_contract.py --adapter-file path/to/adapter.py
   ```

   The checker parses source; it does not import the adapter, load a model, or call audio services.
4. Use [troubleshooting.md](references/troubleshooting.md) when registrations are not discovered, a deploy YAML does not match a pipeline, optional dependencies are missing, or a model test is too expensive.

## Safety rules

- Do CPU/static checks before GPU e2e tests. Full-model examples usually require model checkpoints, CUDA/accelerator hardware, large VRAM, and time.
- Keep custom-pipeline examples self-contained. Do not require future agents to open original examples before implementing a pipeline.
- Treat vendored/upstream model code as parity-sensitive; avoid style rewrites that make future upstream diffs hard.
- If a change touches endpoint contracts, update serving payload guidance in online-serving as well.
- If a change touches deploy topology or defaults, update stage-configuration guidance as well.
