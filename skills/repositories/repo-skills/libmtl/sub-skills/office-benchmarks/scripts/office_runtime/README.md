# LibMTL Office Benchmark Runtime

This installable source package bundles the Office-31 and Office-Home benchmark
launcher, dataloader, and split files distilled from the LibMTL checkout. It is
kept under the runtime skill so future agents do not need to open or depend on
the original repository checkout for the Office workflow.

## Entry points

- Unpackaged script: `../main.py`
- Package module: `python -m libmtl_office_benchmark.main`
- Console script after installation: `libmtl-office`

Install with the sibling `../install_office_runtime.py` script after the LibMTL
CUDA package environment has been prepared.
