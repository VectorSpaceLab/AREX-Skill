# Stage configuration troubleshooting

Use this before asking the user to run expensive model-serving checks. Most failures can be diagnosed by inspecting YAML shape, stage ids, connector names, CLI quoting, and memory budgets.

## Fast triage

```bash
python sub-skills/stage-configuration/scripts/validate_deploy_yaml.py path/to/deploy.yaml
python sub-skills/stage-configuration/scripts/plan_stage_memory.py --num-gpus 2 --gpu-mem-gib 80 --stages 3 --headroom-gib 4 --streaming
```

The validator performs schema and connector sanity checks only. It does not prove that model weights fit or that servers will launch.

## Invalid YAML

Symptoms:

- YAML parser error before the server starts.
- Validator reports `YAML parse failed`, `top-level YAML document must be a mapping`, or `stages must be a list`.

Fixes:

- Use spaces, not tabs.
- Quote device lists: `devices: "0,1"` rather than `devices: 0,1`.
- Use lowercase YAML booleans (`true`, `false`) for portability.
- Ensure a fully materialized deploy file has `stages:`. Thin overlays may omit unchanged stages only when `base_config` resolves.
- Keep `base_config` relative to the overlay file, or use an absolute path that exists in the user's runtime environment.

Bad:

```yaml
stages:
  - stage_id: 0
    devices: 0,1
```

Good:

```yaml
stages:
  - stage_id: 0
    devices: "0,1"
```

## Unknown or missing stage

Symptoms:

- `No stage config found for stage_id=...`.
- A headless process never registers or starts the wrong stage.
- Validator warns about connector keys such as `from_stage_9` or `to_stage_9` when no stage 9 exists.

Fixes:

- Confirm `stage_id` values match the selected pipeline topology.
- If using `pipeline: ...`, ensure the key is the intended registered topology variant.
- Do not invent stage ids in an overlay. Overlays can change fields for existing stages; they do not add model topology unless the selected pipeline supports that topology.
- For head/headless serving, pass the same deploy config to every process and use one process per intended `--stage-id`.

## Connector mismatch

Symptoms:

- Producer stage emits data but consumer stalls.
- Validator reports an input/output connector mismatch for the same edge.
- Missing payload, timeout, or connector `get` failure in logs.

Fixes:

- Every connector referenced under `input_connectors` or `output_connectors` must exist in top-level `connectors`.
- For edge `0 -> 1`, these should agree:

  ```yaml
  stages:
    - stage_id: 0
      output_connectors: {to_stage_1: shm}
    - stage_id: 1
      input_connectors: {from_stage_0: shm}
  ```

- Use `SharedMemoryConnector` only for same-host stages.
- For cross-host stages, use `MooncakeStoreConnector` and confirm `host`, `metadata_server`, `master`, `segment`, `localbuf`, and `proto` fit the deployment.
- Remember that Omni master registration (`--omni-master-address/--omni-master-port`) and connector transport are different paths; both must be reachable.

## Shared memory connector used across hosts

Symptoms:

- Stage processes on different machines cannot read each other's connector payloads.
- Consumer waits for a key that the producer claims to have written.

Fix:

- Replace that edge with a cross-host connector such as `MooncakeStoreConnector`.
- Keep shared memory only for stages on the same physical host/container namespace.

## Mooncake connector cannot initialize

Symptoms:

- Import error for the Mooncake package.
- Connector initialization fails against metadata or master service.
- Timeout waiting for keys even though stage ids and connector names match.

Fixes:

- Confirm the runtime environment includes the Mooncake dependencies.
- Confirm `metadata_server` and `master` are reachable from every stage host.
- Set `host` to the local address that the connector should advertise/use on that host.
- Use `proto: tcp` unless RDMA service, devices, and permissions are already validated.
- Increase `segment`/`localbuf` only after checking host memory; overly small buffers can fail large payloads, while overly large buffers can exhaust host memory.

## OOM at stage initialization

Symptoms:

- Error states free memory is less than desired memory utilization.
- Process exits during model load or vLLM cache allocation.

Fixes:

1. Free GPU memory from other processes.
2. Lower `gpu_memory_utilization` for the failing stage.
3. Move the stage to a different GPU with `devices`.
4. If multiple stages share a GPU, reduce the sum of their `gpu_memory_utilization` values or split them across GPUs.
5. Reduce `max_model_len`, `max_num_seqs`, or `max_num_batched_tokens`.
6. For a large single stage, use `tensor_parallel_size` with a matching multi-GPU `devices` list.
7. For diffusion models, consider VAE tiling/slicing, lower output dimensions, or offload fields only after lowering concurrency.

## OOM during inference after startup succeeds

Symptoms:

- Startup completes, but requests fail under load or with long prompts/media.
- Failures correlate with concurrency, long context, resolution, frame count, or streaming chunks.

Fixes:

- Lower `max_num_seqs` first; it directly reduces simultaneous scheduler capacity.
- Lower `max_num_batched_tokens` for token-heavy prefill.
- Lower `max_model_len` for text/AR stages.
- Lower output resolution, frame count, or diffusion batch size for media stages.
- Enable `vae_use_tiling` or `vae_use_slicing` for VAE-heavy diffusion stages when supported.
- Use CPU/layerwise offload only after acknowledging latency tradeoffs.

## CLI JSON quoting for `--stage-overrides`

Symptoms:

- `--stage-overrides is not valid JSON`.
- Shell strips quotes around stage ids or field names.
- Override silently does not apply because keys are not stringified stage ids.

Correct POSIX shell form:

```bash
--stage-overrides '{"0":{"gpu_memory_utilization":0.50,"max_num_seqs":8}}'
```

Correct PowerShell-style form usually requires escaped inner quotes or a variable; when in doubt, place the JSON in a shell variable and print it before launch.

Checklist:

- JSON keys must be quoted strings: `"0"`, not `0`.
- Use JSON booleans/literals: `true`, `false`, `null`.
- Do not add trailing commas.
- Do not mix YAML syntax inside JSON.

## Precedence surprise

Symptoms:

- YAML value appears ignored.
- Platform section unexpectedly changes a stage.
- A global CLI flag affects all stages.

Remember precedence:

1. Per-stage CLI override JSON or `stage_<id>_<field>` runtime key.
2. Explicit global CLI flags.
3. Platform section for the detected platform.
4. Overlay YAML via `base_config`.
5. Defaults.

Fixes:

- Remove global CLI flags if the YAML should be authoritative.
- Move a global setting into a stage override only for stages that need it.
- Check `platforms.<platform>.stages` for the hardware you are running on.
- Validate the overlay after resolving `base_config`.

## `--stage-id` and head/headless launch errors

Symptoms and fixes:

| Symptom | Fix |
| --- | --- |
| `--stage-id requires both --omni-master-address and --omni-master-port` | Add both flags to head and headless commands. |
| `--omni-replica-address requires --headless` | Remove it from the head process; pass only to headless workers that need bind-address override. |
| `--omni-dp-size-local != 1 requires --stage-id` | Set `--stage-id` or remove the local replica count. |
| `headless mode requires worker_backend=multi_process` | Use the multi-process backend for headless launches. |
| Headless process cannot find its stage | Use the same deploy config and correct stage id; run the validator and check available stage ids. |

## Prohibited vLLM parallel flags under `--omni`

Symptoms:

- Parser rejects upstream vLLM data-parallel or API-server parallel flags with `--omni`.

Fix:

- Configure Omni parallelism through deploy YAML fields (`tensor_parallel_size`, top-level DP/PP, `num_replicas`) and stage/headless flags (`--omni-dp-size-local`) rather than upstream vLLM server data-parallel flags.

## `async_chunk` failures

Symptoms:

- Multi-stage pipeline rejects `async_chunk=True`.
- Downstream stage receives incompatible partial data.
- Streaming output never materializes.

Fixes:

- Use `async_chunk: false` for pipelines that do not declare async-chunk stage processors.
- For single-stage pipelines, do not expect `async_chunk` to create inter-stage overlap.
- Keep producer and consumer connector wiring aligned.
- If disabling async chunk changes latency/streaming behavior, explain that full-payload handoff increases time to first media packet.

## Diffusion parallel config errors

Symptoms:

- Error about `allgather_degree` being mutually exclusive with Ulysses/Ring.
- Error about `ulysses_mode` or `vae_parallel_mode` values.
- Error about HSDP dimensions or HSDP with TP/DP.

Fixes:

- Use only one sequence-parallel family: either `allgather_degree > 1` or Ulysses/Ring degrees.
- Set `ulysses_mode` to `strict` or `advanced_uaa` only.
- Set `vae_parallel_mode` to `tile`, `spatial_shard_height`, or `spatial_shard_width` only.
- Do not combine `use_hsdp: true` with TP or DP in the verified config path.
- If `hsdp_shard_size: -1`, ensure another parallel axis creates a world size and `hsdp_replicate_size` divides it.

## Attention backend or step execution incompatibility

Symptoms:

- Diffusion stage fails in attention kernels.
- Step batching works for one model but not another.
- Mixed causal/full attention path rejects the selected backend.

Fixes:

- Treat `diffusion_attention_backend` and `diffusion_attention_config` as model-specific.
- Fall back to a standard SDPA-style backend when faster kernels reject the attention pattern.
- Disable `step_execution` unless the selected model/recipe explicitly supports it.
- Keep `fa_deterministic` only when the backend supports deterministic mode.

## Offload confusion

Symptoms:

- GPU memory is lower but latency is much worse.
- Model-level CPU offload and layerwise offload are both set.
- Distributed layerwise offload fails with communication errors.

Fixes:

- Prefer reducing concurrency, context length, and media size before offload.
- Do not set `enable_cpu_offload` and `enable_layerwise_offload` together unless accepting layerwise priority and model-specific behavior.
- For distributed layerwise offload, confirm host memory, interconnect bandwidth, rank topology, and `dlo_use_allgather` tradeoffs.
- Increase `dlo_resident_layers` only when GPU memory allows.

## When to stop and ask the user

Ask before live launch or model-running verification when any of these are unknown:

- model cache/download/license state;
- GPU count, memory, or availability;
- whether the deployment is same-host or multi-node;
- Mooncake service addresses/ports;
- acceptable latency tradeoff for offload or reduced concurrency;
- permission to start long-running head/headless server processes.
