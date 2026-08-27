# dm-haiku Troubleshooting

Use this reference for cross-cutting issues before drilling into a sub-skill-specific troubleshooting page.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'haiku'` | The `dm-haiku` distribution is not installed in the active Python. | Run `python -m pip install -U dm-haiku`, then `python scripts/check_haiku_env.py`. Confirm the Python used by the user task is the same Python used for install. |
| `ModuleNotFoundError: No module named 'jax'` or `jaxlib` errors | Haiku expects the user to install a JAX backend separately. | Install a JAX build appropriate for CPU/GPU/TPU, then rerun `scripts/check_haiku_env.py`. CPU JAX is enough for most API debugging. |
| Resolver errors involving the `jax` extra | The package metadata may not match the versions available from the user's package index. | Install JAX explicitly from the JAX installation instructions for the target backend, then install `dm-haiku` without relying on a broad extra. Verify actual imports rather than assuming resolver success. |
| JAX warns that GPUs are present but CUDA-enabled `jaxlib` is not installed | CPU-only JAX is installed on a GPU host. | This is acceptable for Haiku API work. If accelerator execution is required, install the matching CUDA/TPU JAX package and verify `jax.default_backend()` / `jax.devices()`. |
| `ModuleNotFoundError: No module named 'flax'` while using `haiku.experimental.flax` | Flax interop is optional. | Install `flax`, rerun `python scripts/check_haiku_env.py --require-flax`, then use `sub-skills/flax-interop/`. |

## Version and maintenance-mode caveats

- Haiku is best-effort maintained for compatibility. If a new JAX release breaks imports or changes signatures, pin to a known-compatible JAX/Haiku pair or refresh this skill against the newer repo release.
- Do not treat Haiku as a full training stack. Optimizers, datasets, checkpointing, launchers, and distributed job management come from other libraries.
- For new projects with no Haiku dependency, consider whether Flax is a better fit before adding Haiku-specific code.

## Transform and state/RNG failures

| Symptom | Route | First check |
| --- | --- | --- |
| `apply` receives arguments in the wrong order or complains about RNG/state | `sub-skills/core-transforms/` | Compare the selected transform's `init` and `apply` signatures; run the transform smoke script. |
| State is silently missing or an error says to use `transform_with_state` | `sub-skills/core-transforms/` then `sub-skills/params-state-rng/` | Use `hk.transform_with_state` and thread state through apply. |
| `hk.next_rng_key()` fails when `rng=None` | `sub-skills/params-state-rng/` | Pass a non-`None` key to `apply`, or deliberately use `hk.maybe_next_rng_key()` for optional randomness. |
| Raw `jax.vmap`, `jax.scan`, `jax.remat`, or control flow fails inside a transformed function | `sub-skills/jax-interop-and-advanced/` | Replace raw JAX transforms with Haiku wrappers when the inner function touches Haiku params/state/RNG/modules. |

## Example and dataset dependency failures

Haiku's public examples often use external datasets, TensorFlow/TensorFlow Datasets, Optax, RL libraries, accelerators, or long training loops. The generated skill bundles synthetic smoke scripts instead of requiring those full example dependencies:

- Use `sub-skills/modules-and-networks/scripts/haiku_mlp_smoke.py` for a no-download MLP validation.
- Use `sub-skills/params-state-rng/scripts/haiku_rng_state_smoke.py` for parameter/state/RNG validation.
- Use `sub-skills/jax-interop-and-advanced/scripts/haiku_jax_transform_smoke.py` for Haiku wrapper and tree-utility validation.

Only install full example dependencies when the user's task explicitly needs those external datasets or training loops.

## No CLI surface

`dm-haiku` is primarily a Python library and does not expose a package-specific command-line interface. If a user asks for a Haiku CLI command, translate the task into a Python script or notebook workflow and use the bundled smoke helpers for validation.
