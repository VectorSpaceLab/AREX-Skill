#!/usr/bin/env python3
"""Minimal Tensorpack fake-data training smoke.

This helper is self-contained and safe: it does not download data, read the
Tensorpack source tree, or require a GPU. It demonstrates the ModelDesc +
TrainConfig + SimpleTrainer path with callbacks and summaries.
"""

import argparse
import os
import shutil
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a tiny Tensorpack fake-data one-epoch training smoke.")
    parser.add_argument(
        "--workdir",
        required=True,
        help="Directory for Tensorpack logs/checkpoints. Created if missing.")
    parser.add_argument(
        "--steps-per-epoch",
        type=int,
        default=2,
        help="Number of fake-data training steps per epoch. Default: 2.")
    parser.add_argument(
        "--max-epoch",
        type=int,
        default=1,
        help="Number of epochs to run. Default: 1.")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Fake-data batch size. Default: 8.")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete --workdir before running. Only the requested directory is removed.")
    parser.add_argument(
        "--allow-gpu",
        action="store_true",
        help="Do not hide GPUs. By default this CPU smoke sets CUDA_VISIBLE_DEVICES='' before TensorFlow import.")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.steps_per_epoch <= 0:
        raise SystemExit("--steps-per-epoch must be positive")
    if args.max_epoch <= 0:
        raise SystemExit("--max-epoch must be positive")
    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be positive")

    if not args.allow_gpu:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

    # Import TensorFlow/Tensorpack only after optionally hiding GPUs.
    from tensorpack import tfv1 as tf
    from tensorpack import (
        BatchData,
        Conv2D,
        FakeData,
        FullyConnected,
        InferenceRunner,
        MaxPooling,
        ModelDesc,
        ModelSaver,
        ScalarStats,
        ScheduledHyperParamSetter,
        SimpleTrainer,
        TrainConfig,
        argscope,
        launch_train_with_config,
    )
    from tensorpack.tfutils import summary
    from tensorpack.utils import logger

    tf.disable_eager_execution()
    tf.reset_default_graph()
    tf.set_random_seed(1234)

    workdir = Path(args.workdir).expanduser().resolve()
    if args.clean and workdir.exists():
        shutil.rmtree(str(workdir))
    workdir.mkdir(parents=True, exist_ok=True)
    logger.set_logger_dir(str(workdir), action="k")

    image_shape = (16, 16, 1)
    num_classes = 4

    class TinyModel(ModelDesc):
        def inputs(self):
            return [
                tf.TensorSpec((None,) + image_shape, tf.float32, "image"),
                tf.TensorSpec((None, 1), tf.int32, "label"),
            ]

        def build_graph(self, image, label):
            label = tf.reshape(tf.cast(label, tf.int32), [-1], name="label_flat")
            image = tf.cast(image, tf.float32, name="image_float")
            with argscope(Conv2D, kernel_size=3, activation=tf.nn.relu):
                net = Conv2D("conv0", image, 8)
                net = MaxPooling("pool0", net, 2)
                net = Conv2D("conv1", net, 8)
            net = FullyConnected("fc0", net, 16, activation=tf.nn.relu)
            logits = FullyConnected("logits", net, num_classes, activation=tf.identity)
            loss_vec = tf.nn.sparse_softmax_cross_entropy_with_logits(
                logits=logits, labels=label)
            loss = tf.reduce_mean(loss_vec, name="cross_entropy")
            prediction = tf.argmax(logits, axis=1, output_type=tf.int32, name="prediction")
            train_error = tf.reduce_mean(
                tf.cast(tf.not_equal(prediction, label), tf.float32),
                name="train_error")
            summary.add_moving_summary(loss, train_error)
            summary.add_param_summary((".*/W", ["rms"]))
            return tf.identity(loss, name="total_cost")

        def optimizer(self):
            learning_rate = tf.get_variable(
                "learning_rate", initializer=1e-3, trainable=False)
            return tf.train.AdamOptimizer(learning_rate)

    def make_data(size):
        ds = FakeData(
            [image_shape, [1]],
            size,
            random=False,
            dtype=["float32", "int32"],
            domain=[(0.0, 1.0), (0, num_classes)],
        )
        return BatchData(ds, args.batch_size)

    train_df = make_data(args.steps_per_epoch * args.batch_size)
    valid_df = make_data(args.batch_size * 2)

    config = TrainConfig(
        model=TinyModel(),
        dataflow=train_df,
        callbacks=[
            ModelSaver(max_to_keep=2),
            InferenceRunner(valid_df, [ScalarStats("total_cost")]),
            ScheduledHyperParamSetter("learning_rate", [(1, 1e-3)]),
        ],
        steps_per_epoch=args.steps_per_epoch,
        max_epoch=args.max_epoch,
    )
    launch_train_with_config(config, SimpleTrainer())

    checkpoint_file = workdir / "checkpoint"
    print("Tensorpack minimal training smoke completed.")
    print("workdir={}".format(workdir))
    print("checkpoint_index_present={}".format(checkpoint_file.exists()))


if __name__ == "__main__":
    main()
