---
name: stage-configuration
description: "Inspect and tune vLLM-Omni deploy YAMLs, stage placement,
  connectors, memory, CLI precedence, and distributed planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# stage-configuration

Use this sub-skill when a task is about vLLM-Omni pipeline/deploy configuration rather than request payloads or model-family selection.

## Use this for

- Reading or writing a deploy YAML overlay for stages, platforms, connectors, async chunking, dtype, quantization, DP/PP, or stage placement.
- Explaining how `PipelineConfig`, `DeployConfig`, and `StageDeployConfig` combine into effective stage runtime settings.
- Choosing `SharedMemoryConnector` vs `MooncakeStoreConnector` and checking stage input/output connector wiring.
- Planning `devices`, `num_replicas`, `gpu_memory_utilization`, `max_num_seqs`, `max_model_len`, diffusion parallelism, offload, or attention knobs.
- Converting CLI overrides into the correct precedence model: stage overrides > explicit globals > platform section > overlay > defaults.
- Debugging invalid YAML, unknown stage ids, connector mismatch, OOM, or JSON quoting around `--stage-overrides`.

## Start here

1. If the user provides a deploy YAML or overlay, inspect it with the bundled validator:

   ```bash
   python scripts/validate_deploy_yaml.py path/to/deploy.yaml
   ```

2. Read [deploy-schema.md](references/deploy-schema.md) for the self-contained schema, merge rules, precedence, connectors, and CLI examples.
3. Read [memory-and-distributed-placement.md](references/memory-and-distributed-placement.md) for GPU placement, memory-utilization planning, head/headless launch planning, DP/PP/TP/stage replicas, diffusion parallel/offload/attention flags, and multi-node connector decisions.
4. For a quick non-model-loading placement estimate, run:

   ```bash
   python scripts/plan_stage_memory.py \
     --num-gpus 2 --gpu-mem-gib 80 --stages thinker,talker,code2wav --headroom-gib 4 --streaming
   ```

5. If a launch or config fails, use [troubleshooting.md](references/troubleshooting.md) before recommending model downloads or full serving runs.

## Route elsewhere

- HTTP/OpenAI request bodies, `extra_body`, realtime clients, or server endpoint choices belong to the online-serving sub-skill.
- Offline `Omni`/`AsyncOmni` Python scripts, prompt dictionaries, and output field access belong to the offline-inference sub-skill.
- Model-family recipe selection, hardware tables, quantization recipes, and benchmark targets belong to the model-recipes sub-skill.
- Adding new `PipelineConfig` objects, custom diffusion pipelines, or maintainer tests belongs to the model-integration sub-skill.

## Safety and assumptions

- The bundled scripts only parse YAML/arguments and print plans; they do not import vLLM-Omni, load models, contact model hubs, allocate GPUs, or start servers.
- Deploy YAML defaults are package/version dependent. If the user relies on a package-bundled default, keep the overlay minimal and validate the effective structure after resolving `base_config` in the user's environment.
- For live multi-process or multi-node serving, require the user to confirm model cache, GPU capacity, connector services, open ports, and operational budget before launching servers.
