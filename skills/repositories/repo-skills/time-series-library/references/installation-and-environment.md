# Installation and Environment Guidance

TSLib is normally used from a source checkout with `python run.py ...`; it does not expose a package console entry point. Future agents should first identify the user's TSLib checkout or source tree, then run commands from that tree or ensure it is importable through `PYTHONPATH`.

## Recommended base environment

Use Python 3.11 unless the user has a reason to match an older experiment. The public README recommends PyTorch 2.5.1 and CUDA-compatible wheels. A practical base install is:

```bash
conda create -n tslib python=3.11
conda activate tslib
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

Adjust the PyTorch wheel index for the user's driver and CUDA runtime. For CPU-only smoke checks, a CPU PyTorch build is acceptable for core CLI/data/model plumbing, but it is not proof that CUDA benchmark runs or CUDA-only optional models work.

## Minimum checks before running experiments

Use the bundled helpers from this skill directory and point them at the user's TSLib checkout:

```bash
python scripts/check_tslib_environment.py --repo-root /path/to/Time-Series-Library --check-torch --check-core-imports
python scripts/create_tiny_tslib_dataset.py --output /path/to/Time-Series-Library/dataset/tiny-custom/tiny.csv
```

Then, from the user's TSLib checkout, confirm the native parser and use the generated tiny CSV with `--data custom --root_path ./dataset/tiny-custom/ --data_path tiny.csv --target OT --no_use_gpu` for fast data/CLI checks:

```bash
python run.py --help
```

## Optional dependency families

| Capability | Typical extra dependency | Notes |
| --- | --- | --- |
| Mamba/MambaSL models | `mamba_ssm` wheel matching Python, PyTorch, CUDA, Linux ABI | The README shows a CUDA-specific wheel. A mismatched wheel commonly fails at import time. |
| Moirai zero-shot model | `uni2ts --no-deps` plus its transitive runtime stack when needed | Several Moirai paths instantiate pretrained modules and use CUDA in source. |
| Chronos/Chronos2 | `chronos-forecasting` and model access | Source uses `BaseChronosPipeline.from_pretrained(...)`; some paths hard-code CUDA device maps. |
| TimesFM | `timesfm` and model access | Source instantiates a pretrained TimesFM model on CUDA. |
| TiRex | `tirex-ts` and model access | Source loads a remote/pretrained TiRex model. |
| Sundial/TimeMoE | `transformers` and remote-code model access | These paths use `AutoModelForCausalLM.from_pretrained(..., trust_remote_code=True)`. |
| M4 short-term benchmark | `patool`, `huggingface_hub`, M4 files | M4 loaders can fetch files if local files are missing; avoid unintended downloads in smoke tests. |
| UEA classification | `sktime` | Loader expects `DatasetName_TRAIN.ts` and `DatasetName_TEST.ts` or fetches from the Hub. |

Do not install all optional stacks by default. First decide which model family and native verification target the user actually needs.

## Backend selection

- Use `--no_use_gpu` for CPU smoke checks. This sets `args.use_gpu` false even though `run.py` defaults to GPU usage when available.
- Use `--gpu_type cuda` for NVIDIA CUDA and `--gpu_type mps` for Apple Silicon MPS when the installed PyTorch build supports it.
- Many upstream shell recipes export `CUDA_VISIBLE_DEVICES=<id>`. Remove or rewrite that export if the selected GPU id is not available.
- `--use_amp` only makes sense on CUDA paths; do not use it as a generic speed flag.
- Multi-GPU mode uses `--use_multi_gpu --devices 0,1,...`; verify memory and dataset size before launching.

## Docker path

The upstream Dockerfile is CUDA-oriented: PyTorch 2.5.1 with CUDA 12.1, `requirements.txt`, a CUDA-specific `mamba_ssm` wheel, and `uni2ts --no-deps`. Use Docker when the user wants a reproducible GPU environment, but still validate dataset mounts and CUDA visibility before benchmark runs.

## Safe smoke policy

Use these checks before expensive experiments:

1. `python run.py --help` from the user's TSLib checkout to prove parser dependencies import.
2. `python scripts/check_tslib_environment.py --repo-root /path/to/Time-Series-Library --check-core-imports --models DLinear TimesNet TimeXer` from this skill directory to prove core modules import.
3. A tiny local `custom` CSV data-provider check via `sub-skills/data-and-cli/scripts/validate_tslib_data.py` from this skill directory.
4. A CPU command run from the user's TSLib checkout with `--train_epochs 1 --num_workers 0 --batch_size` small and `--no_use_gpu`.

These checks validate command/data/model plumbing. They do not validate full benchmark accuracy, GPU throughput, optional Mamba/LTSM execution, or remote data/model availability.
