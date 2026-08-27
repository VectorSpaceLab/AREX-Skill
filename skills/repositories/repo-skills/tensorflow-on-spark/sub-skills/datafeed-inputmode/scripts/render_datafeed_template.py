#!/usr/bin/env python3
"""Render safe TensorFlowOnSpark DataFeed code templates.

This helper only prints template text. It intentionally does not import, start,
or execute Spark, TensorFlow, TensorFlowOnSpark, network clients, or filesystems.
"""

from __future__ import annotations

import argparse
import re
import sys
import textwrap
from string import Template
from typing import Dict, Iterable


TEMPLATES: Dict[str, Template] = {
    "inference": Template(
        r'''
# Template: InputMode.SPARK one-output-per-input inference
# Fill in load_or_build_model(), row_to_features(), and results_to_python_rows().

def main_fun(args, ctx):
    import numpy as np
    from tensorflowonspark import TFNode

    model = load_or_build_model(args)
    tf_feed = TFNode.DataFeed(ctx.mgr, train_mode=False)

    while not tf_feed.should_stop():
        batch = tf_feed.next_batch($batch_size)
        if len(batch) == 0:
            # Empty batches can occur near EndPartition or final shutdown.
            continue

        # EndPartition can make the final partition batch smaller than batch_size.
        features = np.asarray([row_to_features(row) for row in batch])
        predictions = model(features, training=False)
        results = results_to_python_rows(predictions)

        if len(results) != len(batch):
            raise ValueError(
                "InputMode.SPARK inference requires one output per input; "
                "got {} results for {} inputs".format(len(results), len(batch))
            )
        tf_feed.batch_results(results)


def run_inference(sc, args, input_rdd):
    from tensorflowonspark import TFCluster

    cluster = TFCluster.run(
        sc,
        main_fun,
        args,
        num_executors=args.cluster_size,
        num_ps=0,
        input_mode=TFCluster.InputMode.SPARK,
        master_node="chief",
    )
    try:
        result_rdd = cluster.inference(input_rdd, feed_timeout=$feed_timeout)
        # A Spark action is required; cluster.inference() returns a lazy RDD.
        return result_rdd.collect()
    finally:
        cluster.shutdown()
'''
    ),
    "training": Template(
        r'''
# Template: InputMode.SPARK training generator with terminate() early-stop signal
# Fill in row_to_example(), build_dataset_or_model(), and train_model().

def main_fun(args, ctx):
    import numpy as np
    from tensorflowonspark import TFNode

    tf_feed = TFNode.DataFeed(ctx.mgr)  # training mode is the default

    def rdd_generator():
        while not tf_feed.should_stop():
            batch = tf_feed.next_batch($batch_size)
            if len(batch) == 0:
                return

            features = []
            labels = []
            for row in batch:
                feature, label = row_to_example(row)
                features.append(feature)
                labels.append(label)
            yield np.asarray(features), np.asarray(labels)

    dataset_or_model_input = build_dataset_or_model(rdd_generator, args)
    try:
        train_model(dataset_or_model_input, args)
    finally:
        # Signals Spark feeders to skip later partitions after model completion.
        # It does not cancel the Spark job, so still size num_epochs/partitions carefully.
        tf_feed.terminate()


def run_training(sc, args, train_rdd):
    from tensorflowonspark import TFCluster

    cluster = TFCluster.run(
        sc,
        main_fun,
        args,
        num_executors=args.cluster_size,
        num_ps=0,
        input_mode=TFCluster.InputMode.SPARK,
        master_node="chief",
    )
    try:
        cluster.train(train_rdd, num_epochs=args.epochs, feed_timeout=$feed_timeout)
    finally:
        # Set a positive grace period if the chief exports a model after data feeding.
        cluster.shutdown(grace_secs=getattr(args, "shutdown_grace_secs", 0))
'''
    ),
    "mapped-input": Template(
        r'''
# Template: DataFeed input_mapping for low-level tuple/RDD inputs
# Full Spark ML DataFrame mapping belongs to the spark-ml-pipelines sub-skill.

def main_fun(args, ctx):
    from tensorflowonspark import TFNode

    input_mapping = {
        "features_col": "serving_default_features:0",
        "weights_col": "serving_default_weights:0",
    }
    tf_feed = TFNode.DataFeed(
        ctx.mgr,
        train_mode=False,
        input_mapping=input_mapping,
    )

    while not tf_feed.should_stop():
        batch = tf_feed.next_batch($batch_size)
        if len(batch) == 0:
            continue

        # TensorFlowOnSpark sorts input_mapping by source key before assigning
        # row tuple positions. With the mapping above, each Spark row must be
        # ordered like (features_col_value, weights_col_value).
        features = batch["serving_default_features:0"]
        weights = batch["serving_default_weights:0"]
        results = predict_with_weights(features, weights)

        expected = len(features)
        if len(results) != expected:
            raise ValueError("got {} results for {} inputs".format(len(results), expected))
        tf_feed.batch_results(results)
'''
    ),
    "streaming": Template(
        r'''
# Template: Spark Streaming InputMode.SPARK feed registration
# Fill in parse_row() and main_fun().

def run_streaming_training(sc, args):
    from pyspark.streaming import StreamingContext
    from tensorflowonspark import TFCluster

    ssc = StreamingContext(sc, args.batch_interval_secs)
    stream = ssc.textFileStream(args.input_dir)
    train_dstream = stream.map(parse_row)

    cluster = TFCluster.run(
        sc,
        main_fun,
        args,
        num_executors=args.cluster_size,
        num_ps=1,
        input_mode=TFCluster.InputMode.SPARK,
        log_dir=args.model_dir,
        master_node="chief",
    )

    # Use a long feed timeout for sparse streaming input; e.g. 86400 seconds.
    cluster.train(train_dstream, feed_timeout=$streaming_feed_timeout)
    ssc.start()
    cluster.shutdown(ssc)
'''
    ),
}


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return parsed


def render(template_names: Iterable[str], batch_size: int, feed_timeout: int, streaming_feed_timeout: int) -> str:
    values = {
        "batch_size": str(batch_size),
        "feed_timeout": str(feed_timeout),
        "streaming_feed_timeout": str(streaming_feed_timeout),
    }
    chunks = []
    for name in template_names:
        body = TEMPLATES[name].safe_substitute(values)
        chunks.append("# " + "=" * 76 + "\n" + body.strip() + "\n")
    return "\n".join(chunks)


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print TensorFlowOnSpark InputMode.SPARK DataFeed templates. "
            "The helper is render-only and does not import or run Spark/TensorFlow."
        )
    )
    parser.add_argument(
        "--template",
        choices=["all"] + sorted(TEMPLATES),
        default="all",
        help="Template to print. Default: all.",
    )
    parser.add_argument(
        "--batch-size",
        type=_positive_int,
        default=128,
        help="Literal batch size to place in rendered next_batch() calls.",
    )
    parser.add_argument(
        "--feed-timeout",
        type=_non_negative_int,
        default=600,
        help="Literal feed_timeout seconds to place in static RDD templates.",
    )
    parser.add_argument(
        "--streaming-feed-timeout",
        type=_non_negative_int,
        default=86400,
        help="Literal feed_timeout seconds to place in the streaming template.",
    )
    parser.add_argument(
        "--function-name",
        default="main_fun",
        help="Reserved for future template variants; must be a Python identifier.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available template names and exit.",
    )
    args = parser.parse_args(list(argv))
    if not _IDENTIFIER_RE.match(args.function_name):
        parser.error("--function-name must be a Python identifier")
    return args


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    args = parse_args(argv)
    if args.list:
        for name in sorted(TEMPLATES):
            print(name)
        return 0

    names = sorted(TEMPLATES) if args.template == "all" else [args.template]
    text = render(names, args.batch_size, args.feed_timeout, args.streaming_feed_timeout)
    print(textwrap.dedent(text).rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
