#!/usr/bin/env python3
"""Generate PocketFlow custom dataset/model/run-script skeleton files.

The generated files are templates only. They do not train or download data.
"""

import argparse
from pathlib import Path

DATASET_TEMPLATE = '''"""Dataset helper skeleton for {class_name}."""
import tensorflow as tf
from datasets.abstract_dataset import AbstractDataset

FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_integer('nb_classes', {nb_classes}, '# of classes')
tf.app.flags.DEFINE_integer('nb_smpls_train', 0, '# of samples for training')
tf.app.flags.DEFINE_integer('nb_smpls_val', 0, '# of samples for validation')
tf.app.flags.DEFINE_integer('nb_smpls_eval', 0, '# of samples for evaluation')
tf.app.flags.DEFINE_integer('batch_size', 128, 'batch size per GPU for training')
tf.app.flags.DEFINE_integer('batch_size_eval', 100, 'batch size for evaluation')


def parse_fn(record, is_train):
    """TODO: parse one record into (image, one_hot_label) or task-specific tensors."""
    raise NotImplementedError


class {class_name}(AbstractDataset):
    def __init__(self, is_train):
        super({class_name}, self).__init__(is_train)
        if FLAGS.data_disk == 'local':
            assert FLAGS.data_dir_local is not None, '<FLAGS.data_dir_local> must not be None'
            data_dir = FLAGS.data_dir_local
        elif FLAGS.data_disk == 'hdfs':
            assert FLAGS.data_hdfs_host is not None and FLAGS.data_dir_hdfs is not None
            data_dir = FLAGS.data_hdfs_host + FLAGS.data_dir_hdfs
        else:
            raise ValueError('unrecognized data disk: ' + FLAGS.data_disk)
        # TODO: set file_pattern, dataset_fn, parse_fn, and batch_size.
        self.file_pattern = data_dir
        self.dataset_fn = lambda x: tf.data.TFRecordDataset(x)
        self.parse_fn = lambda x: parse_fn(x, is_train)
        self.batch_size = FLAGS.batch_size if is_train else FLAGS.batch_size_eval
'''

MODEL_TEMPLATE = '''"""ModelHelper skeleton for {model_class}."""
import tensorflow as tf
from nets.abstract_model_helper import AbstractModelHelper
from utils.multi_gpu_wrapper import MultiGpuWrapper as mgw
from {dataset_module} import {dataset_class}

FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_float('nb_epochs_rat', 1.0, '# of training epochs ratio')
tf.app.flags.DEFINE_float('lrn_rate_init', 1e-1, 'initial learning rate')
tf.app.flags.DEFINE_float('batch_size_norm', 128, 'normalization factor of batch size')
tf.app.flags.DEFINE_float('momentum', 0.9, 'momentum coefficient')
tf.app.flags.DEFINE_float('loss_w_dcy', 1e-4, 'weight decay coefficient')


def forward_fn(inputs, is_train, data_format):
    """TODO: build TensorFlow 1.x forward pass and return logits/outputs."""
    raise NotImplementedError


class ModelHelper(AbstractModelHelper):
    def __init__(self, data_format='channels_last'):
        super(ModelHelper, self).__init__(data_format)
        self.dataset_train = {dataset_class}(is_train=True)
        self.dataset_eval = {dataset_class}(is_train=False)

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
        loss += FLAGS.loss_w_dcy * tf.add_n([tf.nn.l2_loss(v) for v in trainable_vars])
        accuracy = tf.reduce_mean(tf.cast(tf.equal(tf.argmax(labels, 1), tf.argmax(outputs, 1)), tf.float32))
        return loss, {{'accuracy': accuracy}}

    def setup_lrn_rate(self, global_step):
        batch_size = FLAGS.batch_size * (1 if not FLAGS.enbl_multi_gpu else mgw.size())
        nb_epochs = 1
        nb_iters = int(FLAGS.nb_smpls_train * nb_epochs * FLAGS.nb_epochs_rat / batch_size)
        return FLAGS.lrn_rate_init, nb_iters

    @property
    def model_name(self):
        return '{model_name}'

    @property
    def dataset_name(self):
        return '{dataset_name}'
'''

RUN_TEMPLATE = '''"""Execution script skeleton for {model_name} at {dataset_key}."""
import traceback
import tensorflow as tf
from {model_module} import ModelHelper
from learners.learner_utils import create_learner

FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_string('log_dir', './logs', 'logging directory')
tf.app.flags.DEFINE_boolean('enbl_multi_gpu', False, 'enable multi-GPU training')
tf.app.flags.DEFINE_string('learner', 'full-prec', "learner's name")
tf.app.flags.DEFINE_string('exec_mode', 'train', 'execution mode: train / eval')
tf.app.flags.DEFINE_boolean('debug', False, 'debugging information')


def main(unused_argv):
    try:
        tf.logging.set_verbosity(tf.logging.DEBUG if FLAGS.debug else tf.logging.INFO)
        sm_writer = tf.summary.FileWriter(FLAGS.log_dir)
        model_helper = ModelHelper()
        learner = create_learner(sm_writer, model_helper)
        if FLAGS.exec_mode == 'train':
            learner.train()
        elif FLAGS.exec_mode == 'eval':
            learner.download_model(); learner.evaluate()
        else:
            raise ValueError('unrecognized execution mode: ' + FLAGS.exec_mode)
        return 0
    except ValueError:
        traceback.print_exc(); return 1


if __name__ == '__main__':
    tf.app.run()
'''


def class_name_from_key(key: str) -> str:
    return ''.join(part.capitalize() for part in key.replace('-', '_').split('_')) + 'Dataset'


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, type=Path, help='Directory where template files will be written')
    parser.add_argument('--dataset-key', required=True, help='Alphanumeric run-script dataset key, e.g. fmnist')
    parser.add_argument('--model-name', required=True, help='Checkpoint model_name value, e.g. convnet')
    parser.add_argument('--dataset-name', help='Checkpoint dataset_name value; defaults to dataset key')
    parser.add_argument('--nb-classes', type=int, default=10)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args(argv)

    if not args.dataset_key.isalnum():
        raise SystemExit('--dataset-key must be alphanumeric to match PocketFlow path parsing')
    dataset_name = args.dataset_name or args.dataset_key
    dataset_class = class_name_from_key(args.dataset_key)
    dataset_file = args.output_dir / f'{args.dataset_key}_dataset.py'
    model_file = args.output_dir / f'{args.model_name}_at_{args.dataset_key}.py'
    run_file = args.output_dir / f'{args.model_name}_at_{args.dataset_key}_run.py'
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for path in [dataset_file, model_file, run_file]:
        if path.exists() and not args.force:
            raise SystemExit(f'{path} exists; pass --force to overwrite')
    dataset_file.write_text(DATASET_TEMPLATE.format(class_name=dataset_class, nb_classes=args.nb_classes), encoding='utf-8')
    model_file.write_text(MODEL_TEMPLATE.format(
        model_class='ModelHelper', dataset_module=dataset_file.stem, dataset_class=dataset_class,
        model_name=args.model_name, dataset_name=dataset_name), encoding='utf-8')
    run_file.write_text(RUN_TEMPLATE.format(
        model_module=model_file.stem, model_name=args.model_name, dataset_key=args.dataset_key), encoding='utf-8')
    print(f'wrote {dataset_file}')
    print(f'wrote {model_file}')
    print(f'wrote {run_file}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
