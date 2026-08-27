# Cross-Cutting Troubleshooting

## Install And Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'pyscenic'` | Package is not installed in the active environment | Install pySCENIC in an isolated environment, then run `python -c "import pyscenic"` and `pyscenic --help`. |
| `ModuleNotFoundError: No module named 'pkg_resources'` from `ctxcore` | Environment has a setuptools release that removed or no longer exposes `pkg_resources` | Install a setuptools release that still provides `pkg_resources`, then rerun import and CLI help checks. |
| `ModuleNotFoundError: No module named 'attr'` | `attrs` is missing even though ctxcore imports `attr` | Install `attrs` and rerun `python -m pip check`, imports, and CLI help. |
| CLI entry point exists but crashes before help | Import dependency failure, incompatible package versions, or incomplete install | Run `python scripts/check_pyscenic_environment.py --check-cli`; fix the first import or dependency error before launching real data. |
| Legacy entry points such as `db2feather`, `invertdb`, or `gmt2regions` are advertised but missing | This checkout's package metadata names scripts that are not present in the source tree | Treat those commands as unavailable unless a release package or separate tool provides them; do not build workflows around them without checking `command --help`. |

## Resource And Data Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Very low overlap between TF list and expression genes | Species, nomenclature, case, Ensembl/HGNC/MGI mapping, or matrix orientation mismatch | Inspect gene IDs before GRN inference; fix symbols or transpose the expression matrix before rerunning. |
| `ctx` cannot open ranking databases | Missing files, old database format, wrong path inside container, or unsupported database extension | Use current ctxcore-compatible Feather v2 ranking databases and ensure every local or cluster worker can read the same paths. |
| Motif annotation columns are missing or filtered to nothing | Wrong motif annotation release, delimiter, species, q-value, or orthology threshold | Validate the TSV columns and thresholds before a full pruning run. |
| AUCell result has unexpected cells/regulons orientation | Text matrix was genes x cells but no transpose flag was used, or output was transposed intentionally | Confirm input orientation and rerun with the correct `--transpose` or dataframe shape. |
| Loom output has wrong cell/gene labels | Non-standard loom attribute names | Pass the correct cell and gene attribute names where the CLI/API supports them. |

## Compute And Operations

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Dask cluster mode fails while local mode works | Workers cannot import the same package stack or cannot access shared resource paths | Use local/custom multiprocessing for one machine, or make package versions and resource mounts identical across workers. |
| Container command cannot find inputs | Host path was not mounted or command uses a path outside the mount | Rewrite all command paths to the container-visible mount path and verify with a read-only listing before running pySCENIC. |
| `@args.txt` command file behaves differently than shell command | Quoting, path expansion, or comments differ from shell parsing | Put one argument per line, avoid shell-only expansion, and test with `pyscenic <subcommand> --help` first. |
| Process is slow or memory-heavy | Large expression matrix, many ranking databases, high worker count, or motif database I/O contention | Lower `--num_workers`, reduce module chunk size, use local SSD/shared storage appropriately, or split workflows into smaller checks before a full run. |

## When To Stop

Stop and ask for user input when required ranking databases or motif annotation files are missing, when running would require a large download, when a cluster/container mount is ambiguous, or when the user asks for a full notebook or benchmark-scale execution without confirming runtime and resources.
