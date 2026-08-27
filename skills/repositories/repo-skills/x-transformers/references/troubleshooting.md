# Troubleshooting

Use this page for install, import, optional backend, and cross-skill failures.

## Install and import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Package does not import | `x-transformers` is not installed in the active Python environment. | Install the package, then rerun `python -c "import x_transformers"`. |
| `pip check` fails | A dependency is missing or incompatible. | Reinstall only the needed extra or rebuild the environment. |
| Optional helper script not found | You are not running from the generated skill tree. | Use the bundled skill tree paths, not the source checkout. |

## Optional backend

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Flash-attention path unavailable | `flash_attn` is not installed or hardware is incompatible. | Use the CPU-safe path first; install the optional extra only when you intentionally need packed-sequence flash behavior. |
| CUDA smoke fails | The active environment does not have a working CUDA runtime. | Use `scripts/probe_backend.py` to confirm the device before enabling CUDA-specific workflows. |

## Core-models failures

- Shape errors in constructor code usually mean the wrong constructor or pooling route was chosen.
- Flash/residual-attention and positional-family conflicts should be fixed by selecting one compatible option family.
- If a `cross_attend` stack fails, check that `context` and `context_mask` are provided together.

## Sequence-workflows failures

- Continuous wrappers usually fail because the input/output dimensions or the mask/lens choice is wrong.
- xVal failures usually mean the token tensor and number tensor do not have identical shapes.
- XL and latent wrappers usually fail because the sequence is too short, the memory settings are incomplete, or paired modules do not match.
- DPO, FreeTransformer, GPTVAE, NeoMLP, and XMLatentDecoder all have wrapper-specific shape and argument constraints; open `sub-skills/sequence-workflows/references/troubleshooting.md` for the detailed table.

## Recipe failures

- Missing `data/enwik8.gz` is expected in a lightweight checkout and is not a package-wide failure.
- Missing extras such as Fire, Accelerate, W&B, tqdm, or optimizer/helper packages usually only affect the long recipes.
- If a native recipe starts training immediately on import, use the bundled copy-task smoke instead of importing the file.

## Fast fallback

If you are unsure where a failure belongs, run:

```bash
python scripts/probe_backend.py
python scripts/smoke_models.py
python sub-skills/training-recipes/scripts/copy_task_smoke.py --steps 1 --device cpu
```

If those pass, the remaining failure is likely route-specific rather than a broken installation.
