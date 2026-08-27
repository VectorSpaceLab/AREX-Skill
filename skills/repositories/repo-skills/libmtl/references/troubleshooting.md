# Troubleshooting

This page collects cross-cutting LibMTL failures that are not specific to one
benchmark dataset.

## Common failure surfaces

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError` for `cvxpy`, `qpsolvers`, `torch_scatter`, or `torch_sparse` | The inspection or runtime environment is incomplete | Install the repo's requirements in a CUDA-capable env and use PyG wheels that match the installed PyTorch build. |
| `Trainer` fails on `cuda:0` | No CUDA device is available | LibMTL's benchmark training path is CUDA-first; use a GPU-backed environment. There is no CPU fallback in `Trainer`. |
| `KeyError` or `TypeError` when passing `EW` / `HPS` class objects to `Trainer` | The current code expects string names, not class objects | Pass `weighting='EW'` and `architecture='HPS'`, or use the example scripts' string-based pattern. |
| `KeyError` for missing `weight_args` or `arch_args` | Direct `Trainer` construction skipped `prepare_args` | Pass both dictionaries explicitly, even if they are empty. |
| `UnboundLocalError` in `prepare_args` for `optim='adagrad'`, `optim='rmsprop'`, `scheduler='cos'`, or `scheduler='exp'` | The parser advertises more options than `prepare_args` currently wires | Use `optim='adam'` or `optim='sgd'` and `scheduler='step'`. |
| Example docs or tests mention older benchmark names | Those names are stale in this checkout | Use the current benchmark workflow guidance and bundled validation scripts. |
| Example import errors from relative modules such as `utils`, `aspp`, or `create_dataset` | The example is being run from the wrong working directory | Run the script from its own example directory or set the example directory on `PYTHONPATH`. |
| Pretrained backbone or tokenizer downloads fail | The example expects network access or a prefilled cache | Download the model once, or point the workflow at a machine with the asset cached. |
| A benchmark script cannot find a bundled split/cache file | The workflow depends on a local artifact such as `random_split.t` or a `cached_feature_*` file | Restore the expected file in the example directory or regenerate the cache with the bundled recipe. |

## Configuration quirks worth remembering

- `set_device(gpu_id)` only sets `CUDA_VISIBLE_DEVICES`; it does not create a
  CPU mode.
- `prepare_args` always prints the effective configuration. This is normal and
  useful for debugging.
- The bilevel methods `MOML`, `FORUM`, and `AutoLambda` are routed through the
  trainer's bilevel path and reuse the `EW` weighting base.

## Legacy XTREME preprocessing note

The raw PAWS-X/XTREME helpers are compatibility sensitive:

- the download step performs a network download;
- the CoNLL helpers assume legacy `networkx` APIs such as `DiGraph.node`.

Treat that preprocessing path as legacy material unless you have a compatible
legacy `networkx` stack or a patched copy.
