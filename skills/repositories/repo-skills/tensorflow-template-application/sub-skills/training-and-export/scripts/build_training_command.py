#!/usr/bin/env python3
"""Build a validated command for the TF1 dense and sparse trainers.

The helper never runs the trainer. It only normalizes flag names, applies a few
source-backed compatibility rules, and prints a shell command or JSON payload.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys

DENSE_ALLOWED_MODELS = {
    "dnn",
    "lr",
    "wide_and_deep",
    "customized",
    "cnn",
    "customized_cnn",
    "lstm",
    "bidirectional_lstm",
    "gru",
}

DENSE_QUEUE_ALLOWED_MODELS = {
    "dnn",
    "lr",
    "wide_and_deep",
    "customized",
    "cnn",
}

SPARSE_ALLOWED_MODELS = {
    "dnn",
    "lr",
    "wide_and_deep",
    "customized",
}

DENSE_LOSSES = {
    "sparse_cross_entropy",
    "cross_entropy",
    "mean_square",
}

DENSE_SCENARIOS = {
    "classification",
    "regression",
}

DENSE_OPTIMIZERS = {
    "sgd",
    "adadelta",
    "adagrad",
    "adam",
    "ftrl",
    "rmsprop",
}

TARGET_SCRIPTS = {
    "dense": "dense_classifier.py",
    "dense-queue": "dense_classifier_use_queue.py",
    "sparse": "sparse_classifier.py",
}

DENSE_FEATURE_SHAPES = {
    "cnn": 9,
    "lstm": 9,
    "bidirectional_lstm": 9,
    "gru": 9,
    "customized_cnn": 262144,
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Build a validated TF1 training/export command.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        allow_abbrev=False,
    )
    parser.add_argument(
        "--target",
        required=True,
        choices=sorted(TARGET_SCRIPTS.keys()),
        help="Which trainer family to target.")
    parser.add_argument(
        "--format",
        choices=("shell", "json"),
        default="shell",
        help="Output format.")

    # Core shared flags.
    parser.add_argument("--mode")
    parser.add_argument("--model")
    parser.add_argument("--scenario")
    parser.add_argument("--loss")
    parser.add_argument("--optimizer")
    parser.add_argument("--optmizier", dest="optmizier")
    parser.add_argument("--learning-rate", "--learning_rate", type=float, dest="learning_rate")
    parser.add_argument("--feature-size", "--feature_size", type=int, dest="feature_size")
    parser.add_argument("--label-size", "--label_size", type=int, dest="label_size")
    parser.add_argument("--epoch-number", "--epoch_number", type=int, dest="epoch_number")
    parser.add_argument("--steps-to-validate", "--steps_to_validate", type=int, dest="steps_to_validate")
    parser.add_argument("--step-to-validate", "--step_to_validate", type=int, dest="step_to_validate")
    parser.add_argument("--checkpoint-path", "--checkpoint_path", dest="checkpoint_path")
    parser.add_argument("--output-path", "--output_path", dest="output_path")
    parser.add_argument("--model-path", "--model_path", dest="model_path")
    parser.add_argument("--model-version", "--model_version", type=int, dest="model_version")
    parser.add_argument("--inference-data-file", "--inference_data_file", dest="inference_data_file")
    parser.add_argument("--inference-result-file", "--inference_result_file", dest="inference_result_file")
    parser.add_argument("--dnn-struct", "--dnn_struct", dest="dnn_struct")
    parser.add_argument("--model-network", "--model_network", dest="model_network")
    parser.add_argument("--train-files", "--train_files", dest="train_files")
    parser.add_argument("--validation-files", "--validation_files", dest="validation_files")
    parser.add_argument("--train-file", "--train_file", dest="train_file")
    parser.add_argument("--validate-file", "--validate_file", dest="validate_file")
    parser.add_argument("--file-format", "--file_format", dest="file_format")
    parser.add_argument("--train-file-format", "--train_file_format", dest="train_file_format")
    parser.add_argument("--input-file-format", "--input_file_format", dest="input_file_format")
    parser.add_argument("--batch-size", "--batch_size", type=int, dest="batch_size")
    parser.add_argument("--train-batch-size", "--train_batch_size", type=int, dest="train_batch_size")
    parser.add_argument("--validation-batch-size", "--validation_batch_size", type=int, dest="validation_batch_size")
    parser.add_argument("--validate-batch-size", "--validate_batch_size", type=int, dest="validate_batch_size")
    parser.add_argument("--batch-thread-number", "--batch_thread_number", type=int, dest="batch_thread_number")
    parser.add_argument("--min-after-dequeue", "--min_after_dequeue", type=int, dest="min_after_dequeue")
    parser.add_argument("--label-type", "--label_type", dest="label_type")
    parser.add_argument("--saved-model-path", "--saved_model_path", dest="saved_model_path")
    parser.add_argument("--dropout-keep-prob", "--dropout_keep_prob", type=float, dest="dropout_keep_prob")
    parser.add_argument("--bn-epsilon", "--bn_epsilon", type=float, dest="bn_epsilon")
    parser.add_argument("--lr-decay-rate", "--lr_decay_rate", type=float, dest="lr_decay_rate")

    # Boolean flags.
    parser.add_argument("--enable-benchmark", "--enable_benchmark", action="store_true", dest="enable_benchmark")
    parser.add_argument("--benchmark-mode", "--benchmark_mode", action="store_true", dest="benchmark_mode")
    parser.add_argument("--enable-bn", "--enable_bn", action="store_true", dest="enable_bn")
    parser.add_argument("--enable-dropout", "--enable_dropout", action="store_true", dest="enable_dropout")
    parser.add_argument("--enable-lr-decay", "--enable_lr_decay", action="store_true", dest="enable_lr_decay")
    parser.add_argument("--resume-from-checkpoint", "--resume_from_checkpoint", action="store_true", dest="resume_from_checkpoint")
    parser.add_argument("--enable-colored-log", "--enable_colored_log", action="store_true", dest="enable_colored_log")

    parser.add_argument(
        "--extra",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help=(
            "Additional raw trainer flags to append. Use KEY=VALUE or KEY. "
            "Repeat the option for multiple extras."),
    )
    return parser.parse_args(argv)


def _first_nonempty(*values):
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _ensure_single(name, *values):
    chosen = _first_nonempty(*values)
    seen = [value for value in values if value not in (None, "")]
    if len({str(value) for value in seen}) > 1:
        raise ValueError("Conflicting values supplied for {}: {}".format(name, seen))
    return chosen


def _flag(name, value):
    if value in (None, "", False):
        return []
    if value is True:
        return ["--{}".format(name)]
    return ["--{}={}".format(name, value)]


def _append_extra(argv, extra_items, emitted_names):
    for item in extra_items:
        item = item.strip()
        if not item:
            raise ValueError("Empty --extra value")
        if "=" in item:
            key, value = item.split("=", 1)
            key = key.strip()
            value = value.strip()
        else:
            key, value = item, None
        if not key:
            raise ValueError("Invalid --extra item: {!r}".format(item))
        if key in emitted_names:
            raise ValueError(
                "--extra contains {} which was already selected by a typed flag".format(
                    key))
        if value is None:
            argv.append("--{}".format(key))
        else:
            argv.append("--{}={}".format(key, value))


def _format_shell(argv):
    return " ".join(shlex.quote(token) for token in argv)


def _warn(warnings, message):
    warnings.append(message)


def _build_dense(args):
    warnings = []
    script = TARGET_SCRIPTS["dense"]
    argv = ["python", script]
    emitted = set()

    mode = _first_nonempty(args.mode)
    if mode:
        if mode not in {"train", "savedmodel", "inference"}:
            raise ValueError("Unsupported dense mode: {}".format(mode))
        argv.extend(_flag("mode", mode))
        emitted.add("mode")

    scenario = _first_nonempty(args.scenario)
    if scenario:
        if scenario not in DENSE_SCENARIOS:
            raise ValueError("Unsupported dense scenario: {}".format(scenario))
        argv.extend(_flag("scenario", scenario))
        emitted.add("scenario")

    loss = _first_nonempty(args.loss)
    if scenario == "regression" and not loss:
        loss = "mean_square"
        _warn(warnings,
              "Dense regression usually needs --loss=mean_square; adding it.")
    if loss:
        if loss not in DENSE_LOSSES:
            raise ValueError("Unsupported dense loss: {}".format(loss))
        argv.extend(_flag("loss", loss))
        emitted.add("loss")

    model = _first_nonempty(args.model)
    if model:
        if model not in DENSE_ALLOWED_MODELS:
            raise ValueError("Unsupported dense model: {}".format(model))
        argv.extend(_flag("model", model))
        emitted.add("model")

    feature_size = _first_nonempty(args.feature_size)
    if model in DENSE_FEATURE_SHAPES:
        required_size = DENSE_FEATURE_SHAPES[model]
        if feature_size is None:
            feature_size = required_size
            _warn(warnings,
                  "{} expects feature_size={}; adding it.".format(
                      model, required_size))
        elif int(feature_size) != required_size:
            raise ValueError(
                "{} expects feature_size={} but got {}".format(
                    model, required_size, feature_size))
    if feature_size is not None:
        argv.extend(_flag("feature_size", feature_size))
        emitted.add("feature_size")

    label_size = _first_nonempty(args.label_size)
    if label_size is not None:
        argv.extend(_flag("label_size", label_size))
        emitted.add("label_size")

    optimizer = _ensure_single("optimizer", args.optimizer, args.optmizier)
    if optimizer:
        if optimizer not in DENSE_OPTIMIZERS:
            raise ValueError("Unsupported optimizer: {}".format(optimizer))
        argv.extend(_flag("optimizer", optimizer))
        emitted.add("optimizer")

    learning_rate = _first_nonempty(args.learning_rate)
    if learning_rate is not None:
        argv.extend(_flag("learning_rate", learning_rate))
        emitted.add("learning_rate")

    dnn_struct = _ensure_single("dnn_struct", args.dnn_struct, args.model_network)
    if dnn_struct is not None:
        argv.extend(_flag("dnn_struct", dnn_struct))
        emitted.add("dnn_struct")

    train_files = _ensure_single("train_files", args.train_files, args.train_file)
    if train_files is not None:
        argv.extend(_flag("train_files", train_files))
        emitted.add("train_files")

    validation_files = _ensure_single("validation_files", args.validation_files,
                                      args.validate_file)
    if validation_files is not None:
        argv.extend(_flag("validation_files", validation_files))
        emitted.add("validation_files")

    file_format = _ensure_single("file_format", args.file_format,
                                 args.input_file_format, args.train_file_format)
    if file_format is not None:
        argv.extend(_flag("file_format", file_format))
        emitted.add("file_format")

    train_batch_size = _ensure_single("train_batch_size", args.train_batch_size,
                                      args.batch_size)
    if train_batch_size is not None:
        argv.extend(_flag("train_batch_size", train_batch_size))
        emitted.add("train_batch_size")

    validation_batch_size = _ensure_single("validation_batch_size",
                                           args.validation_batch_size,
                                           args.validate_batch_size,
                                           args.batch_size)
    if validation_batch_size is not None:
        argv.extend(_flag("validation_batch_size", validation_batch_size))
        emitted.add("validation_batch_size")

    batch_thread_number = _first_nonempty(args.batch_thread_number)
    if batch_thread_number is not None:
        argv.extend(_flag("batch_thread_number", batch_thread_number))
        emitted.add("batch_thread_number")

    epoch_number = _first_nonempty(args.epoch_number)
    if epoch_number is not None:
        argv.extend(_flag("epoch_number", epoch_number))
        emitted.add("epoch_number")

    steps_to_validate = _ensure_single("steps_to_validate", args.steps_to_validate,
                                       args.step_to_validate)
    if steps_to_validate is not None:
        argv.extend(_flag("steps_to_validate", steps_to_validate))
        emitted.add("steps_to_validate")

    checkpoint_path = _first_nonempty(args.checkpoint_path)
    if checkpoint_path is not None:
        argv.extend(_flag("checkpoint_path", checkpoint_path))
        emitted.add("checkpoint_path")

    output_path = _first_nonempty(args.output_path)
    if output_path is not None:
        argv.extend(_flag("output_path", output_path))
        emitted.add("output_path")

    model_path = _first_nonempty(args.model_path)
    if model_path is not None:
        argv.extend(_flag("model_path", model_path))
        emitted.add("model_path")

    model_version = _first_nonempty(args.model_version)
    if model_version is not None:
        argv.extend(_flag("model_version", model_version))
        emitted.add("model_version")

    inference_data_file = _first_nonempty(args.inference_data_file)
    if inference_data_file is not None:
        argv.extend(_flag("inference_data_file", inference_data_file))
        emitted.add("inference_data_file")

    inference_result_file = _first_nonempty(args.inference_result_file)
    if inference_result_file is not None:
        argv.extend(_flag("inference_result_file", inference_result_file))
        emitted.add("inference_result_file")

    if args.enable_benchmark or args.benchmark_mode:
        argv.extend(_flag("enable_benchmark", True))
        emitted.add("enable_benchmark")

    if args.enable_bn:
        argv.extend(_flag("enable_bn", True))
        emitted.add("enable_bn")

    if args.enable_dropout:
        argv.extend(_flag("enable_dropout", True))
        emitted.add("enable_dropout")

    if args.enable_lr_decay:
        argv.extend(_flag("enable_lr_decay", True))
        emitted.add("enable_lr_decay")

    if args.resume_from_checkpoint:
        argv.extend(_flag("resume_from_checkpoint", True))
        emitted.add("resume_from_checkpoint")

    if args.dropout_keep_prob is not None:
        argv.extend(_flag("dropout_keep_prob", args.dropout_keep_prob))
        emitted.add("dropout_keep_prob")

    if args.bn_epsilon is not None:
        argv.extend(_flag("bn_epsilon", args.bn_epsilon))
        emitted.add("bn_epsilon")

    if args.lr_decay_rate is not None:
        argv.extend(_flag("lr_decay_rate", args.lr_decay_rate))
        emitted.add("lr_decay_rate")

    if args.enable_colored_log:
        _warn(warnings,
              "The current dense trainer does not expose enable_colored_log; ignoring it.")

    if args.saved_model_path:
        _warn(warnings,
              "The current dense trainer does not use saved_model_path; ignoring it.")

    _append_extra(argv, args.extra, emitted)
    return script, argv, warnings


def _build_dense_queue(args):
    warnings = []
    script = TARGET_SCRIPTS["dense-queue"]
    argv = ["python", script]
    emitted = set()

    mode = _first_nonempty(args.mode)
    if mode:
        if mode not in {"train", "savedmodel", "inference"}:
            raise ValueError("Unsupported queue dense mode: {}".format(mode))
        argv.extend(_flag("mode", mode))
        emitted.add("mode")

    scenario = _first_nonempty(args.scenario)
    if scenario:
        if scenario not in DENSE_SCENARIOS:
            raise ValueError("Unsupported dense scenario: {}".format(scenario))
        argv.extend(_flag("scenario", scenario))
        emitted.add("scenario")

    loss = _first_nonempty(args.loss)
    if scenario == "regression" and not loss:
        loss = "mean_square"
        _warn(warnings,
              "Dense regression usually needs --loss=mean_square; adding it.")
    if loss:
        if loss not in DENSE_LOSSES:
            raise ValueError("Unsupported dense loss: {}".format(loss))
        argv.extend(_flag("loss", loss))
        emitted.add("loss")

    model = _first_nonempty(args.model)
    if model:
        if model not in DENSE_QUEUE_ALLOWED_MODELS:
            raise ValueError("Unsupported queue dense model: {}".format(model))
        argv.extend(_flag("model", model))
        emitted.add("model")

    feature_size = _first_nonempty(args.feature_size)
    if feature_size is not None:
        argv.extend(_flag("feature_size", feature_size))
        emitted.add("feature_size")

    label_size = _first_nonempty(args.label_size)
    if label_size is not None:
        argv.extend(_flag("label_size", label_size))
        emitted.add("label_size")

    optimizer = _ensure_single("optimizer", args.optimizer, args.optmizier)
    if optimizer:
        if optimizer not in DENSE_OPTIMIZERS:
            raise ValueError("Unsupported optimizer: {}".format(optimizer))
        argv.extend(_flag("optimizer", optimizer))
        emitted.add("optimizer")

    learning_rate = _first_nonempty(args.learning_rate)
    if learning_rate is not None:
        argv.extend(_flag("learning_rate", learning_rate))
        emitted.add("learning_rate")

    dnn_struct = _ensure_single("dnn_struct", args.dnn_struct, args.model_network)
    if dnn_struct is not None:
        argv.extend(_flag("dnn_struct", dnn_struct))
        emitted.add("dnn_struct")

    train_file = _ensure_single("train_file", args.train_file, args.train_files)
    if train_file is not None:
        argv.extend(_flag("train_file", train_file))
        emitted.add("train_file")

    validate_file = _ensure_single("validate_file", args.validate_file,
                                   args.validation_files)
    if validate_file is not None:
        argv.extend(_flag("validate_file", validate_file))
        emitted.add("validate_file")

    train_file_format = _ensure_single("train_file_format", args.train_file_format,
                                       args.file_format, args.input_file_format)
    if train_file_format is not None:
        argv.extend(_flag("train_file_format", train_file_format))
        emitted.add("train_file_format")

    batch_size = _ensure_single("batch_size", args.batch_size, args.train_batch_size)
    if batch_size is not None:
        argv.extend(_flag("batch_size", batch_size))
        emitted.add("batch_size")

    validate_batch_size = _ensure_single("validate_batch_size",
                                         args.validate_batch_size,
                                         args.validation_batch_size)
    if validate_batch_size is not None:
        argv.extend(_flag("validate_batch_size", validate_batch_size))
        emitted.add("validate_batch_size")

    batch_thread_number = _first_nonempty(args.batch_thread_number)
    if batch_thread_number is not None:
        argv.extend(_flag("batch_thread_number", batch_thread_number))
        emitted.add("batch_thread_number")

    min_after_dequeue = _first_nonempty(args.min_after_dequeue)
    if min_after_dequeue is not None:
        argv.extend(_flag("min_after_dequeue", min_after_dequeue))
        emitted.add("min_after_dequeue")

    steps_to_validate = _ensure_single("steps_to_validate", args.steps_to_validate,
                                       args.step_to_validate)
    if steps_to_validate is not None:
        argv.extend(_flag("steps_to_validate", steps_to_validate))
        emitted.add("steps_to_validate")

    checkpoint_path = _first_nonempty(args.checkpoint_path)
    if checkpoint_path is not None:
        argv.extend(_flag("checkpoint_path", checkpoint_path))
        emitted.add("checkpoint_path")

    output_path = _first_nonempty(args.output_path)
    if output_path is not None:
        argv.extend(_flag("output_path", output_path))
        emitted.add("output_path")

    model_path = _first_nonempty(args.model_path)
    if model_path is not None:
        argv.extend(_flag("model_path", model_path))
        emitted.add("model_path")

    model_version = _first_nonempty(args.model_version)
    if model_version is not None:
        argv.extend(_flag("model_version", model_version))
        emitted.add("model_version")

    inference_data_file = _first_nonempty(args.inference_data_file)
    if inference_data_file is not None:
        argv.extend(_flag("inference_data_file", inference_data_file))
        emitted.add("inference_data_file")

    inference_result_file = _first_nonempty(args.inference_result_file)
    if inference_result_file is not None:
        argv.extend(_flag("inference_result_file", inference_result_file))
        emitted.add("inference_result_file")

    if args.enable_benchmark or args.benchmark_mode:
        argv.extend(_flag("enable_benchmark", True))
        emitted.add("enable_benchmark")

    if args.enable_bn:
        argv.extend(_flag("enable_bn", True))
        emitted.add("enable_bn")

    if args.enable_dropout:
        argv.extend(_flag("enable_dropout", True))
        emitted.add("enable_dropout")

    if args.enable_lr_decay:
        argv.extend(_flag("enable_lr_decay", True))
        emitted.add("enable_lr_decay")

    if args.resume_from_checkpoint:
        _warn(warnings,
              "The queue trainer does not expose resume_from_checkpoint; ignoring it.")

    if args.enable_colored_log:
        argv.extend(_flag("enable_colored_log", True))
        emitted.add("enable_colored_log")

    if args.dropout_keep_prob is not None:
        argv.extend(_flag("dropout_keep_prob", args.dropout_keep_prob))
        emitted.add("dropout_keep_prob")

    if args.bn_epsilon is not None:
        argv.extend(_flag("bn_epsilon", args.bn_epsilon))
        emitted.add("bn_epsilon")

    if args.lr_decay_rate is not None:
        argv.extend(_flag("lr_decay_rate", args.lr_decay_rate))
        emitted.add("lr_decay_rate")

    if args.saved_model_path:
        _warn(warnings,
              "The queue trainer does not use saved_model_path; ignoring it.")

    _append_extra(argv, args.extra, emitted)
    return script, argv, warnings


def _build_sparse(args):
    warnings = []
    script = TARGET_SCRIPTS["sparse"]
    argv = ["python", script]
    emitted = set()

    mode = _first_nonempty(args.mode)
    if mode:
        if mode not in {"train", "save_model", "inference", "inference_with_tfrecords", "savedmodel"}:
            raise ValueError("Unsupported sparse mode: {}".format(mode))
        if mode == "savedmodel":
            raise ValueError("Sparse trainer uses mode=save_model, not savedmodel.")
        argv.extend(_flag("mode", mode))
        emitted.add("mode")

    model = _first_nonempty(args.model)
    if model:
        if model not in SPARSE_ALLOWED_MODELS:
            raise ValueError("Unsupported sparse model: {}".format(model))
        argv.extend(_flag("model", model))
        emitted.add("model")
        if model == "lr":
            _warn(warnings,
                  "Sparse lr is fragile because the source path references FLAGS.input_units; verify that branch carefully.")

    feature_size = _first_nonempty(args.feature_size)
    if feature_size is not None:
        argv.extend(_flag("feature_size", feature_size))
        emitted.add("feature_size")

    label_size = _first_nonempty(args.label_size)
    if label_size is not None:
        argv.extend(_flag("label_size", label_size))
        emitted.add("label_size")

    label_type = _first_nonempty(args.label_type)
    if label_type is not None:
        if label_type not in {"int", "float"}:
            raise ValueError("Unsupported sparse label_type: {}".format(label_type))
        argv.extend(_flag("label_type", label_type))
        emitted.add("label_type")

    optimizer = _ensure_single("optimizer", args.optimizer, args.optmizier)
    if optimizer:
        if optimizer not in DENSE_OPTIMIZERS:
            raise ValueError("Unsupported optimizer: {}".format(optimizer))
        argv.extend(_flag("optimizer", optimizer))
        emitted.add("optimizer")

    learning_rate = _first_nonempty(args.learning_rate)
    if learning_rate is not None:
        argv.extend(_flag("learning_rate", learning_rate))
        emitted.add("learning_rate")

    dnn_struct = _ensure_single("model_network", args.model_network, args.dnn_struct)
    if dnn_struct is not None:
        argv.extend(_flag("model_network", dnn_struct))
        emitted.add("model_network")

    train_files = _ensure_single("train_files", args.train_files, args.train_file)
    if train_files is not None:
        argv.extend(_flag("train_files", train_files))
        emitted.add("train_files")

    validation_files = _ensure_single("validation_files", args.validation_files,
                                      args.validate_file)
    if validation_files is not None:
        argv.extend(_flag("validation_files", validation_files))
        emitted.add("validation_files")

    # Sparse current source does not have a file-format flag.
    if any(value not in (None, "") for value in
           (args.file_format, args.train_file_format, args.input_file_format)):
        _warn(warnings,
              "Sparse trainer always reads TFRecords here; file-format flags are ignored.")

    batch_size = _ensure_single("batch_size", args.batch_size, args.train_batch_size)
    if batch_size is not None:
        argv.extend(_flag("train_batch_size", batch_size))
        emitted.add("train_batch_size")
        if args.validation_batch_size is None and args.validate_batch_size is None:
            argv.extend(_flag("validation_batch_size", batch_size))
            emitted.add("validation_batch_size")

    validation_batch_size = _ensure_single("validation_batch_size",
                                           args.validation_batch_size,
                                           args.validate_batch_size)
    if validation_batch_size is not None:
        argv.extend(_flag("validation_batch_size", validation_batch_size))
        emitted.add("validation_batch_size")

    batch_thread_number = _first_nonempty(args.batch_thread_number)
    if batch_thread_number is not None:
        argv.extend(_flag("batch_thread_number", batch_thread_number))
        emitted.add("batch_thread_number")

    min_after_dequeue = _first_nonempty(args.min_after_dequeue)
    if min_after_dequeue is not None:
        argv.extend(_flag("min_after_dequeue", min_after_dequeue))
        emitted.add("min_after_dequeue")

    epoch_number = _first_nonempty(args.epoch_number)
    if epoch_number is not None:
        argv.extend(_flag("epoch_number", epoch_number))
        emitted.add("epoch_number")

    # Sparse does not expose scenario/loss/resume_from_checkpoint in the current path.
    if args.scenario:
        _warn(warnings, "Sparse trainer has no scenario flag; ignoring scenario.")
    if args.loss:
        _warn(warnings, "Sparse trainer uses the sparse cross-entropy branch; ignoring loss.")
    if args.resume_from_checkpoint:
        _warn(warnings,
              "Sparse trainer always restores from the latest checkpoint when needed; ignoring resume_from_checkpoint.")

    checkpoint_path = _first_nonempty(args.checkpoint_path)
    if checkpoint_path is not None:
        argv.extend(_flag("checkpoint_path", checkpoint_path))
        emitted.add("checkpoint_path")

    output_path = _first_nonempty(args.output_path)
    if output_path is not None:
        argv.extend(_flag("output_path", output_path))
        emitted.add("output_path")

    model_path = _first_nonempty(args.model_path)
    if model_path is not None:
        argv.extend(_flag("model_path", model_path))
        emitted.add("model_path")

    saved_model_path = _first_nonempty(args.saved_model_path)
    if saved_model_path is not None:
        argv.extend(_flag("saved_model_path", saved_model_path))
        emitted.add("saved_model_path")
        _warn(warnings,
              "The sparse source keeps saved_model_path in the flag set, but the current save_model path writes to model_path/model_version.")

    model_version = _first_nonempty(args.model_version)
    if model_version is not None:
        argv.extend(_flag("model_version", model_version))
        emitted.add("model_version")

    inference_data_file = _first_nonempty(args.inference_data_file)
    if inference_data_file is not None:
        argv.extend(_flag("inference_test_file", inference_data_file))
        emitted.add("inference_test_file")

    inference_result_file = _first_nonempty(args.inference_result_file)
    if inference_result_file is not None:
        argv.extend(_flag("inference_result_file", inference_result_file))
        emitted.add("inference_result_file")

    if args.benchmark_mode or args.enable_benchmark:
        argv.extend(_flag("benchmark_mode", True))
        emitted.add("benchmark_mode")

    if args.enable_bn:
        argv.extend(_flag("enable_bn", True))
        emitted.add("enable_bn")

    if args.enable_dropout:
        argv.extend(_flag("enable_dropout", True))
        emitted.add("enable_dropout")

    if args.enable_lr_decay:
        argv.extend(_flag("enable_lr_decay", True))
        emitted.add("enable_lr_decay")

    if args.dropout_keep_prob is not None:
        argv.extend(_flag("dropout_keep_prob", args.dropout_keep_prob))
        emitted.add("dropout_keep_prob")

    if args.bn_epsilon is not None:
        argv.extend(_flag("bn_epsilon", args.bn_epsilon))
        emitted.add("bn_epsilon")

    if args.lr_decay_rate is not None:
        argv.extend(_flag("lr_decay_rate", args.lr_decay_rate))
        emitted.add("lr_decay_rate")

    if args.enable_colored_log:
        _warn(warnings, "Sparse trainer does not expose enable_colored_log; ignoring it.")

    _append_extra(argv, args.extra, emitted)
    return script, argv, warnings


def build_command(args):
    if args.target == "dense":
        return _build_dense(args)
    if args.target == "dense-queue":
        return _build_dense_queue(args)
    if args.target == "sparse":
        return _build_sparse(args)
    raise ValueError("Unsupported target: {}".format(args.target))


def main(argv=None):
    args = parse_args(argv)
    try:
        script, command_argv, warnings = build_command(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.format == "json":
        payload = {
            "target": args.target,
            "script": script,
            "argv": command_argv,
            "command": _format_shell(command_argv),
            "warnings": warnings,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    for warning in warnings:
        print("WARNING: {}".format(warning), file=sys.stderr)

    print(_format_shell(command_argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
