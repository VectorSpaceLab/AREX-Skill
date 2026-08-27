# FEDformer Troubleshooting

Use this page when a FEDformer command fails before training, fails during model construction, cannot find data, or produces an unexpected command shape.

## Fast checks

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
python -c "import sympy, einops, scipy; print('wavelet dependencies ok')"
python scripts/run_fedformer.py --repo-root <repo-root> --run -- --help
python scripts/smoke_fedformer.py --repo-root <repo-root> --version Wavelets
```

The FEDformer and Autoformer branches are GPU-first in the verified environment. A CPU import check is not enough to prove this route.

## Failure map

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `torch.cuda.is_available()` is `False` or training immediately falls back to CPU | CUDA wheel or driver is not visible | Use a CUDA-capable PyTorch environment and verify a tiny CUDA tensor allocation before running a training sweep. |
| `ImportError: No module named 'sympy'` | Wavelet filter construction dependency missing | Install `sympy`; the Wavelets path builds Legendre/Chebyshev filters at import/model-construction time. |
| `ImportError: No module named 'einops'` | Wavelet helper dependency missing | Install `einops`; it is imported by the multiresolution layer code. |
| `ImportError` or numeric special-function errors in wavelets | `scipy` missing or incompatible | Install a `scipy` version compatible with the Python/PyTorch stack. |
| KeyError or model-map failure before training | The parser default is `Reformer`, but the model map only contains `FEDformer`, `Autoformer`, `Informer`, and `Transformer` | Always pass `--model FEDformer` or an explicitly supported comparison baseline. |
| Command runs from the wrong directory and imports the root `layers/` tree | The native script expects the working directory to be the FEDformer subtree | Use `scripts/run_fedformer.py` or run native commands from `<repo-root>/FEDformer/`. |
| `FileNotFoundError` for a CSV | `--root_path` and `--data_path` do not point to the same dataset location | Set `--root_path` to the dataset directory and `--data_path` to the CSV filename under that directory. |
| Shape mismatch in embeddings, loss, or prediction output | `features`, `target`, `enc_in`, `dec_in`, or `c_out` do not match the dataset columns | Count the actual input channels and set the three channel flags to match the selected `features` mode. |
| Time feature shape or unsupported frequency error | `--freq` does not match the timestamp cadence | Use `h` for hourly ETT-hour data, `t` for minute data, or a supported Pandas-style cadence that matches the CSV. |
| `--do_predict` fails in the prediction data loader | The pred branch references a prediction dataset class that is not wired in this fork | Treat `--do_predict` as unsupported unless you patch the fork and add a verified prediction loader. |
| `--is_training 0` fails before test-only evaluation | The non-training branch references an argument name that is not defined by the parser | Use the normal train+test path or patch the test-only branch before relying on it. |
| Custom `--moving_avg` crashes model construction | The CLI argument is not list-parsed, while the code expects a real list for multi-kernel decomposition | Leave the default alone, or build the config programmatically and pass a Python list such as `[12, 24]`. |
| Wavelets knobs appear ignored | The command still uses `--version Fourier` | Switch to `--version Wavelets` before tuning `L`, `base`, or `cross_activation`. |
| Fourier mode-selection knobs appear ignored | The command still uses `--version Wavelets` or a non-FEDformer model | Switch to `--version Fourier` with `--model FEDformer`. |

## Dataset alignment checklist

Before launching a long run, confirm:

1. `root_path` contains the CSV named by `data_path`.
2. The CSV has a timestamp column expected by the selected loader.
3. `features` matches the intended forecasting task.
4. `target` exists when using `S` or `MS`.
5. `enc_in`, `dec_in`, and `c_out` match the actual channel count.
6. `seq_len + pred_len` leaves enough rows for train/validation/test splits.

## GPU checklist

1. Verify `torch.cuda.is_available()` is true.
2. Run `scripts/smoke_fedformer.py` before a long sweep.
3. Keep `CUDA_VISIBLE_DEVICES` simple for the first run.
4. Use `--use_multi_gpu --devices 0,1` only after a single-GPU run works.

## Parser caveats

The native parser is usable, but a few defaults are misleading:

- `--model` defaults to `Reformer`, which is invalid for this fork.
- `--use_gpu` is parsed with `type=bool`; shell strings such as `False` are not reliable booleans.
- `--moving_avg` has a Python-list default but is not list-aware when overridden on the command line.
- The pred-only and test-only branches need code review before production use.

When in doubt, start with the wrapper command in `references/workflows.md`, inspect the printed command, and then add `--run` only after the data and device checks pass.
