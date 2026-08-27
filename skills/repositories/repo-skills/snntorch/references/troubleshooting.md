# snnTorch troubleshooting

Use this guide when the package imports but a workflow still fails on shapes, dependencies, backends, or deprecation warnings.

## Fast triage

1. Identify the owning sub-skill from [Workflow map](workflows.md).
2. Check the relevant constructor, signature, or helper pattern in that sub-skill's API reference.
3. Verify the tensor shape convention: many workflows are time-first (`[T, ...]`), while neuron constructors often consume one step at a time.
4. Re-run [`scripts/stack_smoke.py`](../scripts/stack_smoke.py) if the issue might be environmental rather than algorithmic.

## Common symptoms and fixes

| Symptom | Likely cause | Fix | Route |
| --- | --- | --- | --- |
| Import fails because `torch`, `matplotlib`, `nir`, `nirtorch`, `h5py`, or `torchvision` is missing | Optional workflow dependency was not installed | Install the missing package in the same environment as `snntorch`, then rerun the smoke check | Install/import reference |
| CUDA looks available on the host but a CUDA workflow still fails | The installed torch wheel does not match the host driver/toolkit or the module was built on the wrong device | Use a matching CUDA-enabled torch wheel and rerun the optional `--cuda` probe in `scripts/stack_smoke.py` | `core-neurons` / install reference |
| `nn.Sequential` returns too many values or a neuron returns a tuple unexpectedly | A stateful neuron is being used with the wrong `init_hidden` / `output` combination | Use the return contract in `core-neurons` and keep only the final neuron stateful when chaining | `core-neurons` |
| Hidden state leaks across batches or chunks | The model was not reset or detached between independent runs | Use `snntorch.utils.reset(net)` for supported built-ins, or detach the hidden state manually when using custom state handling | `core-neurons` / `encoding-training` |
| `rate()`, `targets_convert()`, or a wrapper loss complains about time axis or batch size | Static and time-varying conventions were mixed, or the target labels do not match the batch dimension | Fix the tensor to the expected shape and rerun the encoding/training smoke helper | `encoding-training` |
| `backprop` prints a deprecation warning | The legacy wrapper is still being used | Prefer a manual training loop for new code; keep the wrapper only when you need its legacy behavior | `encoding-training` |
| `spike_count` fails with tensor labels or weird pandas errors | Labels were passed as a torch tensor instead of a list-like collection | Convert labels to a list of strings or integers before calling `spike_count` | `plotting` |
| `export_to_nir` or `import_from_nir` fails with type inference or shape errors | `sample_data`, `ignore_dims`, or vectorized parameter shapes do not match the live model | Recheck the NIR reference and rerun the bundled NIR smoke | `nir-interoperability` |
| `snntorch.spikevision` emits a deprecation warning | Expected legacy warning | Use it only for old code; for new neuromorphic dataset workflows, migrate to Tonic | `spikevision` |
| `STDPLearner.reset()` raises `AttributeError` | The method is broken in this release | Recreate the learner for a new episode instead of calling `reset()` | `encoding-training` |
| `LeakyParallel(..., device='cuda')` behaves like a mixed-device model | The constructor can create masks on CPU before the module is moved | Construct the module first, then call `.to(device)` | `core-neurons` |
| `spikevision` dataset roots or cache files are not found | The legacy raw-data layout is missing or the cache was not built | Check the expected raw tree and cache names in the spikevision reference | `spikevision` |

## Cross-cutting reminders

- `backprop` and `spikevision` are compatibility surfaces. Prefer the newer or safer path when a fresh workflow is possible.
- `spikeplot` uses matplotlib; headless environments should set `MPLBACKEND=Agg` before importing it.
- `spike_count` expects a list-like label collection whose length matches the output dimension.
- NIR round-trips are most reliable when vector-valued parameters match neuron width and the sample tensor reflects the live forward path.

If the symptom is not listed here, open the owning sub-skill and its bundled references before changing the model or script.
