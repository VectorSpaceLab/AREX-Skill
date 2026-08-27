# Waymax-RL setup and training

## What this workflow is

Waymax-RL is PARL's optional autonomous-driving reinforcement-learning workflow built around a GPU-resident Waymax simulator loop and a PyTorch/rl-games PPO-style trainer. Its purpose is to avoid the CPU↔GPU bottleneck of traditional distributed RL loops: simulation state, JAX/Waymax environment stepping, and learner-side training are intended to stay on the GPU path.

This is not the same operating model as PARL `xparl` CPU actor distribution. `xparl` can run Python actors across trusted machines, but that pattern does not by itself make Waymax simulation and RL updates GPU-resident. For xparl mechanics, use the sibling xparl sub-skill only as a contrast.

## Verification status

This production run did **not** execute Waymax-RL. Runtime verification was blocked by the hard requirements for a CUDA JAX stack, a Waymax checkout at the required revision, and Waymo-format local data. Use this document as an environment and launch checklist, not as proof that the local machine is ready.

## Hard prerequisites

- Python 3.10 environment for the Waymax-RL stack.
- CUDA-capable GPU visible to JAX. A CPU-only JAX install is not a substitute.
- CUDA-compatible JAX installation. The documented local path uses the CUDA 12 extra (`jax[cuda12]`), while the bundled requirements pin `jax==0.6.2`; resolve this deliberately so `jax.devices()` reports a GPU device.
- Waymax installed from its own checkout at commit `71c2be9`.
- TensorFlow GPU package removed or avoided so it does not fight JAX for the GPU. The bundled dependencies use `tensorflow-cpu==2.20`; that CPU package is used by initialization code to inspect devices and set memory-growth behavior, while GPU TensorFlow should not be installed alongside the JAX CUDA runtime unless deliberately tested.
- PyTorch, Hydra/OmegaConf, Brax, Gym, and rl-games matching the Waymax-RL requirements.
- Local Waymo-format TFRecord data. The default `data_path` is a placeholder and must be replaced.

## Installation sequence

Use a fresh environment. Keep the commands below as a sequence; do not mix them into an existing research environment without checking currently installed JAX, TensorFlow, Waymax, and CUDA packages.

1. Create and activate a Python 3.10 environment.
2. Install the CUDA-enabled JAX package for the target CUDA runtime.
3. Verify that JAX can see a GPU before installing the rest of the workflow:

   ```bash
   python - <<'PY'
   import jax
   print(jax.devices())
   assert any(device.platform == "gpu" for device in jax.devices())
   PY
   ```

4. Obtain Waymax separately, check out commit `71c2be9`, and install it editable into the environment.
5. Remove GPU TensorFlow if present:

   ```bash
   python -m pip uninstall -y tensorflow tensorflow-gpu
   ```

6. Install the Waymax-RL requirements. If this reinstalls `tensorflow-cpu`, that is expected for the observed initialization path; verify that no GPU TensorFlow package is active.
7. Prepare a real TFRecord file or directory and edit the Hydra config's `params.config.env_config.data_cfg.data_path`.
8. Run the static config validator before training:

   ```bash
   python ../scripts/validate_waymax_config.py <path-to-hydra-yaml>
   ```

9. Only after the static validator is clean and the GPU/JAX/Waymax/data checks pass, launch the Waymax-RL training entry point with Hydra's `ppo_config` name from the Waymax-RL package directory.

## Runtime architecture

The training entry point follows this structure:

1. Run initialization that sets `XLA_PYTHON_CLIENT_PREALLOCATE=false` and asks TensorFlow to enable GPU memory growth if TensorFlow sees GPUs.
2. Load a Hydra config and convert it to a plain container.
3. Register a rl-games vector environment type named `WAYMAX` and an environment configuration named `waymax`.
4. Build a rl-games `Runner` with a PPO observer.
5. Load the full config into the runner, reset it, and call `runner.run({'train': True})`.

The Waymax environment wrapper then:

- Reads `env_config.data_cfg.data_path`.
- Accepts either a file path or a directory; invalid paths raise an `OSError` during environment construction.
- For `data_type: tfrecord`, builds a Waymax WOD training dataset config using `batch_dims=(num_actors,)`, `max_num_objects`, one path, and 200 points per path.
- Converts nonzero reward weights into a `LinearCombinationRewardConfig`.
- Uses a continuous steering/acceleration action space with a normalized bicycle dynamics model when `action_space.steering_acc: true` and `action_space.is_discrete: false`.
- Wraps the Waymax planning environment in Brax, vectorizes it with `jax.vmap`, auto-resets finished elements, and JIT-compiles reset/step with the configured backend.

## Preflight launch checklist

Before a real run, record the answer to each item:

- Does `jax.devices()` include at least one GPU?
- Does importing Waymax use commit `71c2be9` or the user's explicitly accepted equivalent?
- Does the config validator report `env_config.backend: gpu`?
- Is `data_path` a real file or a directory with the intended TFRecord shards?
- Is the default placeholder path gone?
- Is `num_actors` small enough for the available GPU memory? The default `512` actors and `90` horizon produce a large rollout batch.
- Is `mixed_precision` intended for this GPU?
- If `multi_gpu` is set to true, has the user separately verified rl-games and JAX behavior across the actual devices? The default source config has `multi_gpu: false`.
