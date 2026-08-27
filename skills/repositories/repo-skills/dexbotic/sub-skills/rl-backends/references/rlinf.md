# RLinf integration contract

## Ownership

The Dexbotic-side RLinf flow is conceptually:

```text
Dexbotic Hydra entrypoint
  -> local RL config
  -> Dexbotic model registration
  -> RLinf config validation
  -> RLinf cluster/placement
  -> actor + rollout + environment workers
  -> embodied runner
```

Dexbotic-side modules expose a launcher, a registry bridge, and model adapters. RLinf supplies cluster launch, placement, rollout collection, FSDP actor training, checkpointing, logging, and embodied orchestration.

## Registry and workers

A model adapter should provide an RLinf-compatible builder such as `get_model(cfg, torch_dtype)`. Register a stable `model_type` (the documented examples include `dexbotic_pi0` and `dexbotic_dm0`) through RLinf's model registry. Distributed workers must import the same registry extension module; the documented environment-variable hook is `RLINF_EXT_MODULE` pointing at the Dexbotic registry module. If driver and workers have different registries, config validation may pass while worker construction fails.

## Hydra configs

Task configs compose an environment suite, model config, training backend, PPO/rollout settings, logging, and checkpoint paths. Documented LIBERO suite names include `libero_10`, `libero_90`, `libero_goal`, `libero_object`, and `libero_spatial`. Use explicit overrides for actor and rollout checkpoint paths. Validate that the model type, action space, environment observation schema, and policy adapter agree before starting a cluster.

## Launch marker

The Dexbotic-side integration emits a marker equivalent to `[Dexbotic RL] Launching from Dexbotic entrypoint with RLinf as backend.` before RLinf creates workers. Treat this as a useful log diagnostic, not proof that a rollout completed.

## External boundary

RLinf embodied dependencies, Ray/cluster services, LIBERO/ManiSkill environments, and their assets are not bundled. Use an isolated environment prepared from the external runtime's documentation. Never suggest that a core `import dexbotic` or CUDA tensor allocation verifies RLinf.
