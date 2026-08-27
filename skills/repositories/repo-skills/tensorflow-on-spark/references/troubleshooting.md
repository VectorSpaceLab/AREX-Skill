# Cross-cutting Troubleshooting

Read this when the failure affects installation, imports, Spark/Java availability, TensorFlow/PySpark compatibility, classpaths, or optional GPUs before entering a specific workflow sub-skill.

| Symptom | Likely cause | Recovery | Then read |
|---|---|---|---|
| `ModuleNotFoundError: No module named 'tensorflowonspark'` | Package is not installed in the Python used by `spark-submit` or executors. | Install the package in the driver and executor Python environment; rerun `python scripts/check_environment.py --require tensorflowonspark`. | [API map](api-map.md) |
| `ModuleNotFoundError` for `pyspark`, `tensorflow`, `py4j`, `h5py`, `scipy`, or `numpy` | Runtime dependencies are missing from the active Python. | Install only the missing dependency set needed for the workflow; confirm the executor Python sees the same packages. | Owning sub-skill for the workflow |
| `ModuleNotFoundError: No module named 'pkg_resources'` | TensorFlowOnSpark 2.2.5 imports legacy `pkg_resources`; some modern setuptools versions removed it. | Install a setuptools version that still provides `pkg_resources`, or patch/upgrade the package in a controlled environment. | [cluster-lifecycle](../sub-skills/cluster-lifecycle/SKILL.md) |
| Spark fails with Java class-file version errors | PySpark/Spark was built for a newer Java than the one on `PATH`. | Use the Spark version's documented Java version; rerun `java -version` and `spark-submit --version`. | [cluster-lifecycle troubleshooting](../sub-skills/cluster-lifecycle/references/troubleshooting.md) |
| `Please start a Spark standalone cluster and export MASTER` | Repo-native tests expect a Spark master and separate executor processes. | Use Spark Standalone, YARN, Kubernetes, or `local-cluster[...]` for development; do not treat `local[*]` threads as equivalent. | [cluster-lifecycle](../sub-skills/cluster-lifecycle/SKILL.md) |
| `ClassNotFoundException: org.tensorflow.hadoop.io.TFRecordFileInputFormat` | TensorFlow Hadoop jar is missing from `--jars`, `spark.jars`, or executor classpath. | Add the TensorFlow Hadoop jar to Spark with `--jars` or cluster configuration. | [dataframes-tfrecords](../sub-skills/dataframes-tfrecords/SKILL.md) |
| Cluster hangs waiting for reservations | Not enough executor slots, dynamic allocation, wrong `spark.task.cpus`, duplicate executors, or background worker reuse missing. | Match `num_executors` to the cluster size, set one task per executor, disable dynamic allocation, and inspect reservation logs. | [cluster-lifecycle](../sub-skills/cluster-lifecycle/SKILL.md) |
| Spark-fed inference hangs after output begins | `map_fun` did not call `batch_results` once per input row, an exception is stuck in the error queue, or `feed_timeout` is too low. | Validate the DataFeed loop, output length, exception handling, and timeout. | [datafeed-inputmode](../sub-skills/datafeed-inputmode/SKILL.md) |
| Spark ML pipeline output columns are wrong | `input_mapping` or `output_mapping` keys are mismatched, or code assumed insertion order. | Align mappings with DataFrame columns and TensorFlow tensor/signature names; remember deterministic lexicographic ordering. | [spark-ml-pipelines](../sub-skills/spark-ml-pipelines/SKILL.md) |
| GPU allocation fails or startup waits on a GPU host | No free NVIDIA GPU, Spark resources not assigned, `num_gpus` too high, CUDA TensorFlow not installed, `nvidia-smi` is unavailable, or `tf_args.num_gpus` was omitted so executor startup defaulted to trying one visible GPU. | Treat GPU as optional unless required; set `num_gpus=0` for intentional CPU runs, reduce `num_gpus`, check Spark resource configs, and verify CUDA TensorFlow separately before claiming GPU support. | [cluster-lifecycle](../sub-skills/cluster-lifecycle/SKILL.md) |
| Example command would delete files, download datasets, or start Docker | Repo tutorials include destructive cleanup, downloads, and TF Serving demonstration steps. | Use generated render-only helpers to produce command plans, review with the user, and execute side-effect steps only after explicit approval. | [examples-conversion](../sub-skills/examples-conversion/SKILL.md) |

## Safe diagnostic order

1. Run `python scripts/check_environment.py --json` from this skill directory or pass its path explicitly.
2. Confirm driver and executor Python packages match; mismatch often appears as imports working on the driver but failing in executor logs.
3. Confirm Spark sees Java and the required jar before debugging TensorFlow code.
4. For cluster jobs, debug executor count and reservation logs before changing TensorFlow model code.
5. For data-feed jobs, debug queue input/output counts before changing Spark partitioning.
6. For pipeline jobs, debug DataFrame schema and tensor/signature names before changing `TFEstimator` or `TFModel` parameters.

## Stop conditions

Stop and ask for runtime access or user approval when recovery needs cluster mutation, package upgrades in a shared environment, Docker/TF Serving startup, network dataset downloads, cloud deployment scripts, or GPU-specific package installation.
