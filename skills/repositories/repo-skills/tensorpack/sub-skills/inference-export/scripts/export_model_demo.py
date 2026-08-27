#!/usr/bin/env python3
"""Fake-data Tensorpack export / inference demo.

This script mirrors the shape of the upstream export-model example while
staying self-contained:

- no external images or datasets are needed;
- the training data comes from FakeData;
- the inference graph is separate from the training graph;
- the demo can export SavedModel, export a compact .pb, and run inference.

The runtime Tensorpack imports are done lazily so that ``--help`` works even
before the full Tensorpack dependency set is available.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

SHAPE = 64
CHANNELS = 3
BATCH_SIZE = 1


def _eprint(*parts):
    print(*parts, file=sys.stderr)


def _clean_path(path: Path):
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def _load_runtime():
    try:
        from tensorpack import (
            BatchData,
            FakeData,
            ModelDesc,
            OfflinePredictor,
            PredictConfig,
            QueueInput,
            SimpleTrainer,
            TrainConfig,
            ModelSaver,
            SmartInit,
            launch_train_with_config,
            logger,
            tfv1 as tf,
        )
        from tensorpack.tfutils.export import ModelExporter
    except Exception as exc:  # pragma: no cover - runtime dependency path
        raise RuntimeError(
            "Tensorpack runtime imports failed. This demo needs TensorFlow and the "
            "runtime dependencies that Tensorpack expects."
        ) from exc

    tf.disable_eager_execution()
    return SimpleNamespace(
        tf=tf,
        BatchData=BatchData,
        FakeData=FakeData,
        ModelDesc=ModelDesc,
        OfflinePredictor=OfflinePredictor,
        PredictConfig=PredictConfig,
        QueueInput=QueueInput,
        SimpleTrainer=SimpleTrainer,
        TrainConfig=TrainConfig,
        ModelSaver=ModelSaver,
        SmartInit=SmartInit,
        launch_train_with_config=launch_train_with_config,
        logger=logger,
        ModelExporter=ModelExporter,
    )


def _build_models(tf, ModelDesc):
    class DemoModel(ModelDesc):
        def inputs(self):
            return [
                tf.TensorSpec((None, SHAPE, SHAPE, CHANNELS), tf.uint8, "input_img"),
                tf.TensorSpec((None, SHAPE, SHAPE, CHANNELS), tf.uint8, "target_img"),
            ]

        def make_prediction(self, img):
            img = tf.cast(img, tf.float32)
            img = tf.image.rgb_to_grayscale(img)
            kernel = tf.get_variable(
                "filter",
                dtype=tf.float32,
                initializer=[
                    [[[0.0]], [[1.0]], [[0.0]]],
                    [[[1.0]], [[-4.0]], [[1.0]]],
                    [[[0.0]], [[1.0]], [[0.0]]],
                ],
            )
            return tf.nn.conv2d(img, kernel, strides=[1, 1, 1, 1], padding="SAME")

        def build_graph(self, input_img, target_img):
            target_img = tf.cast(target_img, tf.float32)
            target_img = tf.image.rgb_to_grayscale(target_img)
            self.prediction_img = tf.identity(self.make_prediction(input_img), name="prediction_img")
            cost = tf.losses.mean_squared_error(
                target_img,
                self.prediction_img,
                reduction=tf.losses.Reduction.MEAN,
            )
            return tf.identity(cost, name="total_costs")

        def optimizer(self):
            lr = tf.get_variable("learning_rate", initializer=0.0, trainable=False)
            return tf.train.AdamOptimizer(lr)

    class InferenceOnlyModel(DemoModel):
        def inputs(self):
            return [tf.TensorSpec((None, SHAPE, SHAPE, CHANNELS), tf.uint8, "input_img")]

        def build_graph(self, input_img):
            prediction_img = self.make_prediction(input_img)
            tf.identity(prediction_img, name="prediction_img")

    return DemoModel, InferenceOnlyModel


def _fake_dataset(runtime):
    FakeData = runtime.FakeData
    BatchData = runtime.BatchData
    ds = FakeData(
        [[SHAPE, SHAPE, CHANNELS], [SHAPE, SHAPE, CHANNELS]],
        size=4,
        random=False,
        dtype=["uint8", "uint8"],
        domain=[(0, 255), (0, 255)],
    )
    return BatchData(ds, BATCH_SIZE)


def _demo_inputs():
    base = np.arange(SHAPE * SHAPE * CHANNELS, dtype="uint8").reshape(SHAPE, SHAPE, CHANNELS)
    target = np.flip(base, axis=1).copy()
    return base[None, ...], target[None, ...]


def _train(runtime, workdir: Path):
    tf = runtime.tf
    DemoModel, _ = _build_models(tf, runtime.ModelDesc)
    train_dir = workdir / "train"
    _clean_path(train_dir)
    runtime.logger.set_logger_dir(str(train_dir), action="d")

    ds = _fake_dataset(runtime)
    config = runtime.TrainConfig(
        model=DemoModel(),
        data=runtime.QueueInput(ds),
        callbacks=[runtime.ModelSaver()],
        steps_per_epoch=1,
        max_epoch=1,
    )
    runtime.launch_train_with_config(config, runtime.SimpleTrainer())

    ckpt = tf.train.latest_checkpoint(str(train_dir))
    if not ckpt:
        raise RuntimeError(f"No checkpoint was created in {train_dir}")
    print(f"trained checkpoint: {ckpt}")
    return ckpt


def _predict_config(runtime, ckpt):
    _, InferenceOnlyModel = _build_models(runtime.tf, runtime.ModelDesc)
    return runtime.PredictConfig(
        model=InferenceOnlyModel(),
        session_init=runtime.SmartInit(ckpt),
        input_names=["input_img"],
        output_names=["prediction_img"],
    )


def _export_serving(runtime, workdir: Path, ckpt):
    export_dir = workdir / "exported-serving"
    _clean_path(export_dir)
    pred_config = _predict_config(runtime, ckpt)
    runtime.ModelExporter(pred_config).export_serving(str(export_dir))
    saved_model = export_dir / "saved_model.pb"
    if not saved_model.exists():
        raise RuntimeError(f"SavedModel export did not create {saved_model}")
    print(f"saved model: {export_dir}")
    return export_dir


def _export_compact(runtime, workdir: Path, ckpt):
    compact_path = workdir / "compact_graph.pb"
    _clean_path(compact_path)
    pred_config = _predict_config(runtime, ckpt)
    runtime.ModelExporter(pred_config).export_compact(str(compact_path))
    if not compact_path.exists():
        raise RuntimeError(f"Compact export did not create {compact_path}")
    print(f"compact graph: {compact_path}")
    return compact_path


def _apply(runtime, workdir: Path, ckpt, compact_path: Path):
    tf = runtime.tf
    pred_config = _predict_config(runtime, ckpt)
    predictor = runtime.OfflinePredictor(pred_config)
    input_batch, _ = _demo_inputs()
    offline_output = predictor(input_batch)[0]

    output_dir = workdir / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    offline_path = output_dir / "offline_prediction.npy"
    np.save(offline_path, offline_output)

    with tf.Session(config=tf.ConfigProto(allow_soft_placement=True)) as sess:
        with tf.gfile.GFile(str(compact_path), "rb") as fh:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(fh.read())
            tf.import_graph_def(graph_def)
        input_tensor = sess.graph.get_tensor_by_name("import/input_img:0")
        output_tensor = sess.graph.get_tensor_by_name("import/prediction_img:0")
        compact_output = sess.run(output_tensor, {input_tensor: input_batch})

    compact_path_out = output_dir / "compact_prediction.npy"
    np.save(compact_path_out, compact_output)

    print(f"offline prediction: {offline_path}")
    print(f"compact prediction: {compact_path_out}")
    print(f"offline shape: {offline_output.shape}")
    print(f"compact shape: {compact_output.shape}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Fake-data Tensorpack export demo with train, export, and apply phases."
    )
    parser.add_argument(
        "--workdir",
        required=True,
        help="Directory that will receive the training logs and exported artifacts",
    )
    parser.add_argument(
        "--run",
        default="all",
        choices=["train", "export-compact", "export-serving", "apply", "all"],
        help="Which phase to run",
    )
    args = parser.parse_args(argv)

    workdir = Path(args.workdir).expanduser().resolve()
    workdir.mkdir(parents=True, exist_ok=True)

    try:
        runtime = _load_runtime()
    except Exception as exc:
        _eprint(f"error: {exc}")
        return 2

    state = {"ckpt": None}

    def ensure_checkpoint():
        if state["ckpt"] is not None:
            return state["ckpt"]
        train_dir = workdir / "train"
        existing = runtime.tf.train.latest_checkpoint(str(train_dir))
        if existing:
            state["ckpt"] = existing
            return state["ckpt"]
        state["ckpt"] = _train(runtime, workdir)
        return state["ckpt"]

    def ensure_serving():
        _export_serving(runtime, workdir, ensure_checkpoint())
        return workdir / "exported-serving"

    def ensure_compact():
        _export_compact(runtime, workdir, ensure_checkpoint())
        return workdir / "compact_graph.pb"

    try:
        if args.run in {"train", "all"}:
            ensure_checkpoint()
        if args.run in {"export-serving", "all"}:
            ensure_serving()
        if args.run in {"export-compact", "all"}:
            ensure_compact()
        if args.run in {"apply", "all"}:
            _apply(runtime, workdir, ensure_checkpoint(), ensure_compact())
    except Exception as exc:
        _eprint(f"error: {exc}")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
