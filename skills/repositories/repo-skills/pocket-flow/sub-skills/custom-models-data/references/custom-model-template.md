# Custom Model and Dataset Template

Read this when creating a new PocketFlow task. The pattern is distilled from the Fashion-MNIST-style example and the built-in `nets/*_run.py` files, but this reference is self-contained.

## File set to create in a PocketFlow checkout

A custom task usually needs three Python modules:

| File role | Purpose |
| --- | --- |
| Dataset helper | Loads train/eval records and returns TensorFlow 1.x iterators. |
| Model helper | Defines forward pass, loss/metrics, learning-rate schedule, and model/dataset names. |
| Run script | Defines common flags, creates the helper, creates the learner, and dispatches train/eval. |

Use the bundled [generate_model_helper_skeleton.py](../scripts/generate_model_helper_skeleton.py) to generate starter files outside this skill tree.

## Dataset helper skeleton

Core requirements:

- Import TensorFlow 1.x and the abstract dataset base.
- Define dataset-specific flags such as `nb_classes`, sample counts, and batch sizes.
- In `__init__(is_train)`, call the base constructor and choose a data path from `FLAGS.data_disk`.
- For file-backed datasets, set `file_pattern`, `dataset_fn`, `parse_fn`, and `batch_size`.
- For in-memory datasets, override `build()` while preserving the same return contract.

Pseudocode:

```python
class MyDataset(AbstractDataset):
    def __init__(self, is_train):
        super(MyDataset, self).__init__(is_train)
        if FLAGS.data_disk == 'local':
            assert FLAGS.data_dir_local is not None
            data_dir = FLAGS.data_dir_local
        elif FLAGS.data_disk == 'hdfs':
            assert FLAGS.data_hdfs_host is not None and FLAGS.data_dir_hdfs is not None
            data_dir = FLAGS.data_hdfs_host + FLAGS.data_dir_hdfs
        else:
            raise ValueError('unrecognized data disk: ' + FLAGS.data_disk)
        self.file_pattern = ...
        self.batch_size = FLAGS.batch_size if is_train else FLAGS.batch_size_eval
        self.dataset_fn = ...
        self.parse_fn = lambda record: parse_fn(record, is_train)
```

## ModelHelper skeleton

Core requirements:

- Call `AbstractModelHelper.__init__(data_format, forward_w_labels=False)`.
- Instantiate dataset objects in the constructor, but do not create TensorFlow ops there.
- Keep training/evaluation forward passes separate when batch-norm, dropout, or augmentation differs.
- Return `(loss, metrics)` from `calc_loss`; metrics should be TensorFlow scalar tensors.
- Compute `nb_iters` from sample count, epochs, and effective batch size.
- Keep `model_name` and `dataset_name` stable because they influence checkpoint archive names.

Pseudocode:

```python
class ModelHelper(AbstractModelHelper):
    def __init__(self, data_format='channels_last'):
        super(ModelHelper, self).__init__(data_format)
        self.dataset_train = MyDataset(is_train=True)
        self.dataset_eval = MyDataset(is_train=False)

    def build_dataset_train(self, enbl_trn_val_split=False):
        return self.dataset_train.build(enbl_trn_val_split)

    def build_dataset_eval(self):
        return self.dataset_eval.build()

    def forward_train(self, inputs):
        return forward_fn(inputs, is_train=True, data_format=self.data_format)

    def forward_eval(self, inputs):
        return forward_fn(inputs, is_train=False, data_format=self.data_format)

    def calc_loss(self, labels, outputs, trainable_vars):
        loss = tf.losses.softmax_cross_entropy(labels, outputs)
        metrics = {'accuracy': accuracy_tensor}
        return loss, metrics

    def setup_lrn_rate(self, global_step):
        batch_size = FLAGS.batch_size * (1 if not FLAGS.enbl_multi_gpu else mgw.size())
        return lrn_rate, nb_iters
```

## Run script skeleton

The run script is what users pass to a PocketFlow launch mode. It should define common flags and no heavy side effects at import time.

```python
tf.app.flags.DEFINE_string('log_dir', './logs', 'logging directory')
tf.app.flags.DEFINE_boolean('enbl_multi_gpu', False, 'enable multi-GPU training')
tf.app.flags.DEFINE_string('learner', 'full-prec', "learner's name")
tf.app.flags.DEFINE_string('exec_mode', 'train', 'execution mode: train / eval')
tf.app.flags.DEFINE_boolean('debug', False, 'debugging information')

def main(unused_argv):
    sm_writer = tf.summary.FileWriter(FLAGS.log_dir)
    model_helper = ModelHelper()
    learner = create_learner(sm_writer, model_helper)
    if FLAGS.exec_mode == 'train':
        learner.train()
    elif FLAGS.exec_mode == 'eval':
        learner.download_model()
        learner.evaluate()
    else:
        raise ValueError('unrecognized execution mode: ' + FLAGS.exec_mode)

if __name__ == '__main__':
    tf.app.run()
```

## Checklist before selecting a learner

- The run script name contains the right dataset key for `path.conf`.
- `build_dataset_train()` and `build_dataset_eval()` return tensors matching `forward_*()` expectations.
- Classification labels are one-hot with width `FLAGS.nb_classes`.
- Detection helpers set `forward_w_labels=True` only when the selected learner supports label-aware forward calls.
- The model exposes prunable/quantizable TensorFlow variables and operations if selecting compression learners.
- A full-precision pilot can train/evaluate before adding compression.
