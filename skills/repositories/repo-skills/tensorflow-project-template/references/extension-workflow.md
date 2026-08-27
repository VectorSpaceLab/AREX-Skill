# Extension Workflow

## Purpose

Read this when creating a real project from the template: replacing the example model, trainer, and data generator while keeping the base loop, config, logging, and checkpoint conventions understandable.

## End-to-end adaptation checklist

1. Copy the template project and keep the top-level layout recognizable: `base/`, `models/`, `trainers/`, `data_loader/`, `utils/`, `configs/`, and `mains/`.
2. Decide whether the project will stay TensorFlow 1.x graph-mode or be ported to TensorFlow 2.x/Keras. The original source is TF1-style.
3. Add or update a JSON config with all fields needed by the model, trainer, data loader, logger, and checkpoint paths.
4. Implement a child model that inherits `BaseModel` and creates graph tensors/ops in `build_model()`.
5. Implement a child trainer that inherits `BaseTrain` and consumes the model/data contracts in `train_step()` and `train_epoch()`.
6. Replace or extend `DataGenerator` so it yields batches matching the model placeholders.
7. Wire a `main` file that parses config, creates output directories, constructs the TensorFlow session and objects, optionally loads a checkpoint, and starts training.
8. Run `scripts/check_template_static.py` from this skill against the copied project, then run `scripts/run_tiny_training_smoke.py` if a TF1-compatible runtime is available.

## Model pattern

Create a new file under your copied project's `models/` directory. A model class should own graph construction and saver setup.

```python
from base.base_model import BaseModel
import tensorflow as tf


class MyModel(BaseModel):
    def __init__(self, config):
        super(MyModel, self).__init__(config)
        self.build_model()
        self.init_saver()

    def build_model(self):
        self.is_training = tf.placeholder(tf.bool)
        self.x = tf.placeholder(tf.float32, shape=[None] + self.config.state_size)
        self.y = tf.placeholder(tf.float32, shape=[None, self.config.num_classes])

        logits = ...  # build graph from self.x
        self.loss = ...
        self.train_step = tf.train.AdamOptimizer(self.config.learning_rate).minimize(
            self.loss,
            global_step=self.global_step_tensor,
        )
        self.accuracy = ...

    def init_saver(self):
        self.saver = tf.train.Saver(max_to_keep=self.config.max_to_keep)
```

Keep the attributes consumed by the trainer stable (`x`, `y`, `is_training`, training op, metrics) or update the trainer at the same time.

## Trainer pattern

Create a matching trainer under `trainers/`. It should own batch iteration, `sess.run(...)`, metric aggregation, logging, and save cadence.

```python
from base.base_train import BaseTrain
import numpy as np
from tqdm import tqdm


class MyTrainer(BaseTrain):
    def __init__(self, sess, model, data, config, logger):
        super(MyTrainer, self).__init__(sess, model, data, config, logger)

    def train_epoch(self):
        losses = []
        accs = []
        for _ in tqdm(range(self.config.num_iter_per_epoch)):
            loss, acc = self.train_step()
            losses.append(loss)
            accs.append(acc)

        step = self.model.global_step_tensor.eval(self.sess)
        self.logger.summarize(step, summaries_dict={
            "loss": np.asarray(np.mean(losses)),
            "acc": np.asarray(np.mean(accs)),
        })
        self.model.save(self.sess)

    def train_step(self):
        batch_x, batch_y = next(self.data.next_batch(self.config.batch_size))
        feed_dict = {
            self.model.x: batch_x,
            self.model.y: batch_y,
            self.model.is_training: True,
        }
        _, loss, acc = self.sess.run(
            [self.model.train_step, self.model.loss, self.model.accuracy],
            feed_dict=feed_dict,
        )
        return loss, acc
```

The example logger expects summary values with a `.shape` attribute; wrapping metric scalars with `np.asarray(...)` avoids plain-float failures.

## Data generator pattern

The example `DataGenerator` is not a real loader. A replacement should document and test:

- Input tensor shape expected by the model.
- Label shape and dtype.
- Whether sampling is random, sequential, shuffled, or epoch-aware.
- What `next_batch(batch_size)` returns.
- How training and validation/test splits are exposed if needed.

A compatible minimal contract is:

```python
class MyDataGenerator:
    def __init__(self, config):
        self.config = config
        # load or create arrays/dataset handles here

    def next_batch(self, batch_size):
        # yield or return a generator that yields (batch_x, batch_y)
        yield batch_x, batch_y
```

If you switch to `tf.data.Dataset`, update the trainer so it uses dataset iterators instead of `next(self.data.next_batch(...))`.

## Main wiring pattern

A main file should make object dependencies explicit:

```python
import tensorflow as tf
from data_loader.data_generator import DataGenerator
from models.my_model import MyModel
from trainers.my_trainer import MyTrainer
from utils.config import process_config
from utils.dirs import create_dirs
from utils.logger import Logger
from utils.utils import get_args


def main():
    args = get_args()
    config = process_config(args.config)
    create_dirs([config.summary_dir])
    # If config.checkpoint_dir is a filename prefix, create its parent directory.

    sess = tf.Session()
    data = DataGenerator(config)
    model = MyModel(config)
    logger = Logger(sess, config)
    trainer = MyTrainer(sess, model, data, config, logger)
    model.load(sess)
    trainer.train()
```

Prefer explicit exception handling around config parsing and imports. The original `mains/example.py` catches all exceptions and exits with `0`, which can hide real failures in automated runs.

## Validation strategy

Use three levels of checks:

1. Static template check: file presence, class hooks, config keys, and TF1 API usage.
2. Tiny smoke: one batch/one epoch in a temporary work directory with synthetic data.
3. Project-specific test: a real but bounded fixture from the target dataset or model family.

Do not run long training or overwrite real experiment directories just to prove the template wiring.

## Common extension decisions

| Decision | Recommended handling |
|---|---|
| Add new config values | Add them to the JSON and document defaults before reading them from model/trainer/data code. |
| Change number of classes | Change label shape in the model and data generator together; avoid hard-coded `10` unless it remains true. |
| Change input shape | Update `state_size`, data generator output, and model placeholder/layers together. |
| Add validation metrics | Extend `train_epoch()` or add a separate eval method; choose `summarizer="test"` for test writer output. |
| Change checkpoint layout | Make `save()` and `load()` agree on directory versus filename prefix semantics. |
| Port to TensorFlow 2.x | Treat it as a source migration, not a dependency upgrade; replace top-level TF1 APIs or use `tf.compat.v1` consistently. |
