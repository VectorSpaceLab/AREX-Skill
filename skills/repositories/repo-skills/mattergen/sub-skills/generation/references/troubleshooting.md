# Generation troubleshooting

Diagnose in order: request syntax → asset/config validity → imports/backend →
small generation → scaled generation → artifact completeness.

| Symptom | Likely cause | Action |
|---|---|---|
| `Either pretrained_name or model_path must be provided` | No checkpoint selector | Supply exactly one selector. |
| `Only one of pretrained_name or model_path` | Both selectors supplied | Remove one; a local path takes no Hub name. |
| `No checkpoints found` / `No last.ckpt found` | Wrong local directory or unhydrated LFS | Point to the checkpoint root containing config and hydrated `.ckpt`; run LFS hydration or use an explicitly authorized Hub download. |
| Checkpoint file is about 100 bytes or starts with an LFS pointer | Git-LFS object is not present | Do not run; fetch the selected checkpoint object and verify its size/content. |
| Hub download fails | Network, auth/cache, or wrong model name | Confirm the exact catalog name, cache permissions, and network. Do not silently substitute a different model. |
| `ModuleNotFoundError` for `ase`, `pymatgen`, `torch_geometric`, Hydra, or related package | Incomplete or incompatible install | Run public import/help probes in the intended environment; install the package's compatible runtime dependencies rather than patching the generated helper. |
| CUDA/PyG device error | Wrong torch/PyG wheel or unavailable device | Compare torch and PyG backend builds, run a tiny CUDA tensor/extension smoke, then select CPU/MPS only if the workflow's performance is acceptable. |
| MPS operation unsupported | Backend limitation | Set `PYTORCH_ENABLE_MPS_FALLBACK=1` where appropriate, reduce the smoke case, or use CUDA. Do not claim CUDA verification from MPS. |
| `properties_to_condition_on` Fire parse error | Unquoted mapping or whitespace around `:` | Quote the whole mapping: `"{'energy_above_hull':0.05,'chemical_system':'Li-O'}"`. The safe helper accepts a normalized mapping string and reports parse errors before running. |
| Condition assertion says a property was not trained | Checkpoint/model mismatch | Select a checkpoint whose config declares every requested property; adding a config override cannot create a trained embedding. |
| Property value has wrong type/range or chemical system is malformed | Input semantics, not sampler failure | Check the property embedding's expected representation and use examples from the checkpoint/model documentation; start with one known supported target. |
| CSP says sampling config contains `atomic_numbers` | Normal config used for fixed composition | Use `sampling_config_name=csp` and a CSP-trained checkpoint. Do not delete sampler parts ad hoc. |
| CSP composition is ignored or empty | Target list syntax or missing composition loader | Use the native Fire list syntax or the helper's repeated mapping options; ensure each composition has positive integer counts. |
| `AssertionError` about batch size/num batches | Neither constructor nor `generate` received both | Set positive `batch_size` and `num_batches`; total work is their product. |
| CUDA out-of-memory | Batch or trajectory footprint too large | Lower `batch_size` first, then `num_batches`; disable `record_trajectories`; retry in a new output directory. |
| Job is unexpectedly slow | CPU/MPS, large diffusion/sample count, or excessive trajectory work | Confirm selected device, begin with one sample, and use the model-card throughput only for rough planning. |
| Guidance has no effect or samples are unrealistic | Zero guidance, unsupported condition, or overly strong scale | Confirm the condition is trained, use guidance 0/1 as baselines, then increase gradually; guidance is not a guarantee of target satisfaction. |
| `config_overrides` Hydra error | Wrong key, missing `+`/`++`, or incompatible checkpoint config | Revert to baseline, add one documented override at a time, and preserve the exact resolved config. |
| Sampling config not found | Wrong directory/name or a file extension passed as name | `sampling_config_path` is a directory and `sampling_config_name` is the YAML basename (`default` or `csp`). |
| Permission/no-space error writing results | Output path unavailable or contains partial artifacts | Choose a writable directory with space; do not overwrite an incomplete run without checking it. |
| ZIP exists but structure count is wrong | Interrupted run or conversion failure | Count CIF members and extxyz frames, compare with requested total, and rerun the failed batch separately. |
| Trajectory ZIP is huge | `record_trajectories=True` stores intermediate states | Disable it for production unless denoising paths are needed for analysis. |

## Two-stage stop rules

**CUDA but no checkpoint:** report backend readiness and asset absence
separately. Stop before `from_hf_hub` unless the user explicitly authorizes
network/cache acquisition; do not launch a generation job from CUDA readiness
alone.

**Malformed multi-condition CSP request:** parse and correct the mapping/list
first. Then verify that the checkpoint is CSP-trained and that `csp` is selected.
A normal conditional model with `chemical_system` and `energy_above_hull` is not
a CSP model simply because it has a composition-like target in the request.
