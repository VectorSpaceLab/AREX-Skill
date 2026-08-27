# API Reference

## Purpose

Read this when you need exact class responsibilities, method names, expected config fields, and verified runtime facts for a project based on TensorFlow Project Template. These facts are distilled from the README, source files, and a live import probe in a TensorFlow 1.15-compatible inspection environment.

## Public source modules

The template has no `setup.py`, `pyproject.toml`, or package metadata. Imports work when the project root is on `PYTHONPATH` or the current working directory is the project root. The main public modules are:

| Module | Important objects | Role |
|---|---|---|
| `base.base_model` | `BaseModel` | Shared model counters, checkpoint save/load, abstract graph/saver hooks. |
| `base.base_train` | `BaseTrain` | Shared session initialization and epoch loop. |
| `models.example_model` | `ExampleModel` | Concrete TF1 graph example. |
| `models.template_model` | `TemplateModel` | Empty child-model skeleton. |
| `trainers.example_trainer` | `ExampleTrainer` | Concrete training epoch/step example. |
| `trainers.template_trainer` | `TemplateTrainer` | Empty child-trainer skeleton. |
| `data_loader.data_generator` | `DataGenerator` | Minimal batch generator. |
| `utils.config` | `get_config_from_json`, `process_config` | JSON-to-namespace config parsing and derived experiment paths. |
| `utils.dirs` | `create_dirs` | Directory creation helper. |
| `utils.logger` | `Logger` | TensorBoard summary writer wrapper. |
| `utils.utils` | `get_args` | CLI parser for `--config`. |

## `BaseModel`

Source: `base/base_model.py`.

Construction:

```python
model = ChildModel(config)
```

A child model should call `super(...).__init__(config)`, then call its own `build_model()` and `init_saver()`.

Important behavior:

- `self.config` stores the parsed config namespace.
- `init_global_step()` creates `self.global_step_tensor = tf.Variable(0, trainable=False, name="global_step")` under `tf.variable_scope("global_step")`.
- `init_cur_epoch()` creates `self.cur_epoch_tensor` and `self.increment_cur_epoch_tensor` under `tf.variable_scope("cur_epoch")`.
- `save(sess)` calls `self.saver.save(sess, self.config.checkpoint_dir, self.global_step_tensor)`.
- `load(sess)` calls `tf.train.latest_checkpoint(self.config.checkpoint_dir)` and restores it when present.
- `init_saver()` and `build_model()` raise `NotImplementedError` in the base class.

Checkpoint path caution: `save()` treats `config.checkpoint_dir` as a TensorFlow save path prefix, while `load()` treats it as a checkpoint directory. In a robust project, prefer a directory for loading and a filename prefix for saving, or adjust the base class so both methods agree.

## `ExampleModel`

Source: `models/example_model.py`.

Constructor:

```python
model = ExampleModel(config)
```

Expected config fields:

- `state_size`: list appended after the batch axis for `x`, e.g. `[784]`.
- `learning_rate`: optimizer learning rate.
- `max_to_keep`: passed to `tf.train.Saver(max_to_keep=...)`.

Graph objects created by `build_model()`:

- `is_training = tf.placeholder(tf.bool)`.
- `x = tf.placeholder(tf.float32, shape=[None] + config.state_size)`.
- `y = tf.placeholder(tf.float32, shape=[None, 10])`.
- Dense layer `dense1`: `tf.layers.dense(x, 512, activation=tf.nn.relu, name="dense1")`.
- Dense layer `dense2`: `tf.layers.dense(d1, 10, name="dense2")`.
- `cross_entropy`: mean softmax cross entropy.
- `train_step`: Adam optimizer minimize op with `global_step=self.global_step_tensor`.
- `accuracy`: mean accuracy from argmax predictions.
- `saver`: `tf.train.Saver(max_to_keep=config.max_to_keep)`.

The example is shape-specific: labels are hard-coded as ten classes and data must match `state_size`.

## `BaseTrain`

Source: `base/base_train.py`.

Constructor signature verified by inspection:

```python
BaseTrain(sess, model, data, config, logger)
```

Construction stores all five objects, creates `self.init = tf.group(tf.global_variables_initializer(), tf.local_variables_initializer())`, and immediately runs it in the provided session.

`train()` loops:

```python
for cur_epoch in range(model.cur_epoch_tensor.eval(sess), config.num_epochs + 1, 1):
    self.train_epoch()
    sess.run(model.increment_cur_epoch_tensor)
```

The upper bound is inclusive because of `num_epochs + 1`. If `cur_epoch_tensor` starts at `0` and `num_epochs` is `10`, this executes eleven epochs. Adjust this before using the template for production experiments if ten exact epochs are intended.

`train_epoch()` and `train_step()` are abstract hooks that raise `NotImplementedError`.

## `ExampleTrainer`

Source: `trainers/example_trainer.py`.

Constructor signature verified by inspection:

```python
ExampleTrainer(sess, model, data, config, logger)
```

Expected model attributes:

- `x`, `y`, and `is_training` placeholders.
- `train_step`, `cross_entropy`, and `accuracy` tensors/ops.
- `global_step_tensor` for summary step.
- `save(sess)` method.

Expected data contract:

```python
batch_x, batch_y = next(data.next_batch(config.batch_size))
```

The bundled `DataGenerator.next_batch()` yields one sampled batch per call. If you replace it with a persistent iterator or dataset object, update `ExampleTrainer.train_step()` accordingly.

`train_epoch()`:

1. Iterates `range(config.num_iter_per_epoch)` through `tqdm`.
2. Calls `train_step()` each iteration.
3. Averages losses and accuracies with `np.mean`.
4. Calls `logger.summarize(cur_it, summaries_dict={"loss": loss, "acc": acc})`.
5. Calls `model.save(sess)`.

## `DataGenerator`

Source: `data_loader/data_generator.py`.

The example implementation is synthetic:

- `input`: `np.ones((500, 784))`.
- `y`: `np.ones((500, 10))`.
- `next_batch(batch_size)` randomly samples `batch_size` rows and yields one `(input, y)` batch.

For real data, preserve the trainer-visible return shape or update the trainer and model together.

## Config helpers

Source: `utils/config.py`.

```python
config, config_dict = get_config_from_json(json_file)
config = process_config(json_file)
```

`get_config_from_json()` reads JSON, converts it to `bunch.Bunch`, and returns both the namespace and raw dictionary. `process_config()` then adds:

- `summary_dir = os.path.join("../experiments", config.exp_name, "summary/")`
- `checkpoint_dir = os.path.join("../experiments", config.exp_name, "checkpoint/")`

Those paths are relative to the process current working directory, not to the config file.

## Logger

Source: `utils/logger.py`.

Constructor:

```python
logger = Logger(sess, config)
```

Creates two TensorBoard writers:

- `config.summary_dir/train`
- `config.summary_dir/test`

`summarize(step, summarizer="train", scope="", summaries_dict=None)` chooses the train or test writer and lazily creates one summary placeholder/op per tag.

Important detail: the implementation expects each value in `summaries_dict` to have a `.shape` attribute. NumPy scalars and arrays satisfy this; plain Python floats do not. Convert Python floats with `np.asarray(value)` or change the logger before passing ordinary floats.

## CLI helper

Source: `utils/utils.py`.

`get_args()` defines one optional argument:

```bash
-c C, --config C
```

The default is the string `'None'`; `mains/example.py` catches all exceptions while parsing/processing config and prints `missing or invalid arguments` before exiting with code `0`. Treat that broad catch as a template simplification, not robust CLI error handling.
