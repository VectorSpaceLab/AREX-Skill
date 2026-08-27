# TensorFlowOnSpark API Map

Use this map to choose the nearest sub-skill before reading detailed references.

| Surface | Public objects or files | Owner | Notes |
|---|---|---|---|
| Cluster lifecycle | `TFCluster.run`, `TFCluster.TFCluster.train`, `TFCluster.TFCluster.inference`, `TFCluster.TFCluster.shutdown`, `TFCluster.TFCluster.tensorboard_url` | [cluster-lifecycle](../sub-skills/cluster-lifecycle/SKILL.md) | Startup/reservation and shutdown are separated from DataFeed row semantics. |
| Executor context | `TFSparkNode.TFNodeContext`, `ctx.absolute_path`, `ctx.start_cluster_server`, `ctx.get_data_feed`, `ctx.release_port` | [cluster-lifecycle](../sub-skills/cluster-lifecycle/SKILL.md) | User `map_fun(args, ctx)` code receives this context. |
| Data feed queues | `TFNode.DataFeed`, `next_batch`, `should_stop`, `batch_results`, `terminate`, `marker.EndPartition` | [datafeed-inputmode](../sub-skills/datafeed-inputmode/SKILL.md) | Raw RDD/DStream feed and inference output contracts. |
| Spark ML pipeline | `pipeline.TFEstimator`, `TFModel`, `Namespace`, `TFParams`, param mixins, `yield_batch` | [spark-ml-pipelines](../sub-skills/spark-ml-pipelines/SKILL.md) | DataFrame train/transform APIs and SavedModel inference. |
| TFRecord/DataFrame utility | `dfutil.saveAsTFRecords`, `loadTFRecords`, `toTFExample`, `infer_schema`, `fromTFExample` | [dataframes-tfrecords](../sub-skills/dataframes-tfrecords/SKILL.md) | Requires TensorFlow Hadoop Input/OutputFormat classes on Spark classpath. |
| Independent executor jobs | `TFParallel.run` | [cluster-lifecycle](../sub-skills/cluster-lifecycle/SKILL.md) | One TensorFlow function per executor without shared DataFeed queues. |
| GPU/environment helpers | `gpu_info.is_gpu_available`, `gpu_info.get_gpus`, `util.single_node_env`, Spark resource API handling | [cluster-lifecycle](../sub-skills/cluster-lifecycle/SKILL.md) | GPU allocation is optional unless explicitly required. |
| Example conversion | MNIST Keras/Estimator, ResNet, segmentation, saved_model_cli, TF Serving command patterns | [examples-conversion](../sub-skills/examples-conversion/SKILL.md) | Render command plans and conversion checklists, not destructive cleanup or downloads. |

## Compatibility notes

- TensorFlowOnSpark 2.2.5 targets TensorFlow 2.x examples; TensorFlow 1.x users generally need the older package tag and compatible examples.
- The package's source uses `pkg_resources`; modern environments where `pkg_resources` is removed from `setuptools` need a compatible setuptools installation or a package update.
- Spark-native checks need Java and a Spark runtime. Spark local threads are not a full substitute for executor-process behavior.
- The generated skill documents CPU-compatible paths by default and treats CUDA as optional unless the user requests GPU execution.
