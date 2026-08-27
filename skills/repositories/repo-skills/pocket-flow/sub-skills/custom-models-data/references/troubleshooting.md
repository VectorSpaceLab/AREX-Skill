# Custom Model and Data Troubleshooting

| Symptom / error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `TypeError: __init__() missing ... data_format` | `ModelHelper` did not call `AbstractModelHelper.__init__` with a data format. | Call `super(ModelHelper, self).__init__('channels_last')` or another supported format. |
| TensorFlow ops appear before learner graph construction | Dataset/model helper constructor created TensorFlow tensors or layers too early. | Constructors should instantiate helpers and store settings only; build ops in `build_dataset_*` and `forward_*`. |
| `FLAGS.data_dir_local must not be None` | `path.conf` key does not match the run script's dataset key or launcher did not pass path args. | Validate config with [execution-config/scripts/validate_path_conf.py](../../execution-config/scripts/validate_path_conf.py). |
| Shape mismatch in first convolution | Dataset parser emits wrong layout or `data_format` mismatch. | Emit NHWC by default. If using `channels_first`, transpose before NCHW layers and verify the model supports it. |
| `ValueError` from MobileNet helper about data format | MobileNet built-in supports `channels_last` only. | Use `channels_last` or choose/adapt another model helper. |
| Softmax cross entropy complains about labels/logits shapes | `nb_classes` flag, one-hot labels, or final dense layer width mismatch. | Keep `FLAGS.nb_classes`, parser one-hot width, and model output width aligned. |
| Compression learner fails on detection helper | Some compression learners call `forward_train(inputs)` and do not pass labels/objects. | Start with `full-prec`; verify learner compatibility before applying compression to `forward_w_labels=True` helpers. |
| Pretrained model archive name unexpected | `model_name` or `dataset_name` changed. | Archive names use `models_<model_name>_at_<dataset_name>.tar.gz`; keep stable names or update model URL contents. |
| Duplicate TensorFlow flag errors | Multiple modules define the same `tf.app.flags` in one process. | Run one task module per process; use unique experimental flag names. |
| HDFS path concatenation wrong | `data_hdfs_host` or `data_dir_hdfs` missing/slashed incorrectly. | Ensure host and path combine into a valid HDFS URI and only select HDFS when accessible. |

## Debugging order

1. Import the dataset/model/run script with `--help` to confirm flags register.
2. Validate `path.conf` and dataset key.
3. Build a tiny parser/unit smoke if the data format permits a small fixture.
4. Run a full-precision pilot before compression.
5. Add one compression learner at a time.
