# Cross-cutting troubleshooting

## Import and environment

- **`ModuleNotFoundError` for a repository module:** this project is not
  packaged. Run entry points from the checkout or add that checkout explicitly
  to `PYTHONPATH`; do not install a similarly named third-party package.
- **Torch imports but CUDA is false:** install a CUDA-enabled PyTorch/torchvision
  pair compatible with the host driver, then verify `torch.cuda.is_available()`
  and a one-element CUDA allocation. The repo's core operational paths use
  `cuda` directly, so do not silently downgrade a training or sampling claim to
  CPU.
- **`torchvision` operator/version errors:** align torch and torchvision builds;
  do not mix a CPU torchvision wheel with a CUDA torch wheel.
- **`train.py --help` or `sample.py --help` raises
  `ValueError: unsupported format character '#'`:** the `--logstyle` help text
  contains `%#.#f` and `%#.#e`, which argparse interprets as formatting tokens.
  Inspect options through `utils.prepare_parser()` or invoke the script with a
  concrete configuration; patch the help string to `%%#.#f`/`%%#.#e` only in a
  deliberate source-maintenance change.

## Data and configuration

- **Unknown dataset key / `KeyError`:** use one of the keys in
  `references/model-overview.md`. Adding a new dataset requires a loader in
  `datasets.py` plus consistent `dset_dict`, `imsize_dict`, `root_dict`,
  `nclass_dict`, and `classes_per_sheet_dict` entries.
- **Zero images in ImageFolder:** the root must contain one directory per class
  with supported image extensions. Remove stale index `.npz` files after
  changing class layout.
- **HDF5 key or shape error:** validate that `imgs` is uint8 NCHW and `labels`
  is one-dimensional int64 with the same first dimension. Use the bundled
  HDF5 validator before training.
- **Inception moments not found:** prepare them for the same base dataset name
  used by sampling. The metric code intentionally fails early when the `.npz`
  is absent; do not fabricate moments.

## Runtime and checkpoints

- **Out-of-memory:** lower `batch_size`, `G_batch_size`, channel widths,
  resolution, or accumulation settings. `--load_in_mem` is a host-RAM choice,
  not a GPU-memory fix; the README warns that ImageNet HDF5 can require roughly
  96 GB or more.
- **Missing checkpoint file:** the experiment name, `weights_root`, and suffix
  must match the training run. `best0`, `copy0`, and an empty suffix are not
  interchangeable.
- **State/config mismatch:** use `--config_from_name` only when the saved
  experiment metadata is authoritative, and preserve compatible model,
  resolution, class count, latent, EMA, and normalization settings.
- **SyncBN or `--cross_replica` instability:** this repository documents that
  its custom synchronized variants can cripple training. Start with built-in
  batch normalization and enable cross-replica only for a controlled experiment.
- **Metric disagreement:** this code uses torchvision's Inception and explicitly
  labels its IS/FID as unofficial. Use the separate legacy TF1 path only when
  reproducing the repository's official comparison protocol.
