# Office Benchmark Workflows

This reference covers the self-contained multi-input image classification
runtime for Office-31 and Office-Home.

## Self-contained runtime artifacts

The Office workflow is bundled inside this sub-skill and does not require the
original repository checkout:

- `scripts/main.py` — unpackaged launcher that adds the bundled source package
  to `PYTHONPATH` and runs the benchmark.
- `scripts/install_office_runtime.py` — installation entry point for the
  bundled runtime package.
- `scripts/office_runtime/` — installable source package
  `libmtl-office-benchmark` with the launcher, dataloader, and split files.
- `scripts/check_office_data.py` — layout checker for raw images, split files,
  and optionally the runtime package data.

## Installation entry point

Install the main LibMTL CUDA environment first, then install the self-contained
Office runtime package from this sub-skill directory:

```bash
python scripts/install_office_runtime.py --python "$(command -v python)"
```

By default this installs only the bundled runtime package with `--no-deps` so it
cannot accidentally replace an already prepared CUDA PyTorch stack. If the user
is intentionally building an environment from scratch and accepts dependency
resolution, pass `--with-deps`.

After installation, the console script is available as:

```bash
libmtl-office --help
```

The runtime can also be launched without installation through the unpackaged
script:

```bash
python scripts/main.py --help
```

## Typical command pattern

Run from this sub-skill directory, or use absolute paths to the bundled scripts:

```bash
python scripts/main.py --weighting EW --arch HPS --dataset office-31 --dataset_path /path/to/office --gpu_id 0 --multi_input --mode train --save_path /tmp/libmtl-office
```

After installing the runtime package, the equivalent console entry point is:

```bash
libmtl-office --weighting EW --arch HPS --dataset office-31 --dataset_path /path/to/office --gpu_id 0 --multi_input --mode train --save_path /tmp/libmtl-office
```

For Office-Home, switch `--dataset office-home` and keep the rest of the layout
consistent.

## Important flags

- `--dataset` selects the task family.
- `--dataset_path` points at the raw image root.
- `--bs` is shared across train, val, and test dataloaders.
- `--multi_input` must remain enabled.
- `--mode` toggles training versus test-only execution.
- `--office_num_workers` controls dataloader workers in the bundled runtime.

## Shared data pipeline

The bundled source package loads split files from its own
`libmtl_office_benchmark/data_txt/` package data. It no longer calls
`LibMTL.utils.get_root_dir()` or reads split files from an external checkout.
The package uses those splits to create one dataloader per domain/task.

## Shared model wiring

- The encoder is a ResNet-18 backbone followed by a small projection block.
- Each task uses a linear decoder sized to the number of classes for the chosen
  dataset family.
- The runtime still uses the shared LibMTL `Trainer`, so CUDA is required.

## Workflow checks

1. Confirm the dataset family matches the split files.
2. Confirm every referenced image exists under the raw data root.
3. Run `python scripts/check_office_data.py DATASET IMAGE_ROOT --check-runtime-package`.
4. Use `python scripts/main.py --help` to verify the unpackaged launcher.
5. Use `python scripts/install_office_runtime.py --python "$(command -v python)"`
   when the installed `libmtl-office` entry point is needed.
6. Confirm the pretrained backbone is cached or downloadable.
