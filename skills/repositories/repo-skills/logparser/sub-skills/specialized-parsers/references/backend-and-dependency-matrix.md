# Backend and dependency matrix

## Purpose

Use this table before installing or running a specialized parser. It shows the
extra dependency, runtime, or backend assumption that makes the parser special.

| Parser | Extra dependency / backend | Why it is special | Safe verification path |
| --- | --- | --- | --- |
| SHISO | `nltk`; import shim for the installed `logparser/SHISO` directory | package import is not fully relative | `scripts/run_shiso_with_import_shim.py` |
| SLCT | GCC with relaxed warning handling | legacy C helper needs compilation flags that work on the current host | `scripts/run_slct_safe.py` |
| LogCluster | Perl runtime | Perl-backed wrapper around the upstream tool | import + tiny parse smoke |
| MoLFI | `deap` | evolutionary search parser | tiny parse smoke or import check |
| NuLog | `torch`, `torchvision`, `keras_preprocessing`; CUDA available but not required | torch-based parser with old pandas/NumPy assumptions | `scripts/run_nulog_smoke.py` |
| DivLog | `openai`, `tiktoken`, `matplotlib`, `plotly`, `tenacity`, plus API credentials | live API calls and benchmark maps | import-only check unless credentials are available |

## Notes

- A CUDA-capable GPU is available on the host, but NuLog also works as a CPU
  parser once the NumPy/pandas compatibility pins are corrected.
- API-backed parsing is not the same as a GPU backend; DivLog depends on
  credentials and network access instead.
- The shared install script reports whether `gcc`, `perl`, and `torch.cuda` are
  available.
