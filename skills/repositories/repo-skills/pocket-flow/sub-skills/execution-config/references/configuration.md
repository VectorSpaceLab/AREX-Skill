# Configuration

PocketFlow launchers read `path.conf` as simple `key = value` lines.

## Parsing rules

- Lines starting with `#` are comments.
- Inline comments after `#` are ignored.
- Blank lines are skipped.
- `None` means "unset" and is not forwarded into the launcher preview.
- The dataset name comes from the run script suffix `at_<dataset>_run.py`.

## Keys used by the execution launcher

| Key | Meaning | Preview output |
| --- | --- | --- |
| `data_hdfs_host` | HDFS host for remote input pipelines | `--data_hdfs_host <value>` |
| `model_http_url` | HTTP/HTTPS root for pretrained model download | `--model_http_url <value>` |
| `data_dir_local_<dataset>` | Local dataset directory | normalized to `--data_dir_local` |
| `data_dir_docker_<dataset>` | Docker-visible dataset directory | normalized to `--data_dir_local` |
| `data_dir_seven_<dataset>` | Seven-visible dataset directory | normalized to `--data_dir_local` |
| `data_dir_hdfs_<dataset>` | HDFS dataset directory | `--data_dir_hdfs <value>` |

For example, `nets/resnet_at_cifar10_run.py` maps to the `cifar10` dataset slot.

## Preview behavior

The bundled validator mirrors the source launchers while staying non-destructive:

- it normalizes the chosen mode-specific dataset path to `--data_dir_local`
- it forwards `data_hdfs_host` and `model_http_url` when present
- it keeps other non-`data_dir_*` settings as `--key value`
- it reports missing or ambiguous keys before any training begins

If you only have `path.conf.template`, the validator can still show the expected command shape and mark missing values explicitly.

## Recommended flow

1. Copy `path.conf.template` to `path.conf`.
2. Fill in the keys for the dataset and mode you plan to use.
3. Run `python scripts/validate_path_conf.py --mode local --script nets/resnet_at_cifar10_run.py --conf path.conf`.
4. Fix the missing entries that the preview reports.
5. Use `check_runtime.py` if the config looks correct but the launcher still fails.
