#!/usr/bin/env python3
"""Tiny fixture probe for TensorFlowOnSpark dfutil TFRecord helpers.

Default mode runs a pure conversion smoke test. Spark mode adds a local
DataFrame ↔ TFRecord round trip and checks for the TensorFlow Hadoop input and
output classes.
"""

import argparse
import json
import os
import shutil
import sys
import tempfile


def _fail(message):
    raise RuntimeError(message)


def _assert(condition, message):
    if not condition:
        _fail(message)


def _runtime_modules():
    try:
        from pyspark.sql import Row
        from pyspark.sql.types import ArrayType
        from pyspark.sql.types import BinaryType
        from pyspark.sql.types import DoubleType
        from pyspark.sql.types import LongType
        from pyspark.sql.types import StringType
        from pyspark.sql.types import StructField
        from pyspark.sql.types import StructType
    except Exception as exc:  # pragma: no cover - environment guard
        raise RuntimeError("PySpark is required for this probe.") from exc

    try:
        import tensorflow as tf
    except Exception as exc:  # pragma: no cover - environment guard
        raise RuntimeError("TensorFlow is required for this probe.") from exc

    try:
        from tensorflowonspark import dfutil
    except Exception as exc:  # pragma: no cover - environment guard
        raise RuntimeError("TensorFlowOnSpark is required for this probe.") from exc

    return {
        "Row": Row,
        "ArrayType": ArrayType,
        "BinaryType": BinaryType,
        "DoubleType": DoubleType,
        "LongType": LongType,
        "StringType": StringType,
        "StructField": StructField,
        "StructType": StructType,
        "tf": tf,
        "dfutil": dfutil,
    }


def _sample_dtypes():
    return [
        ("title", "string"),
        ("count", "int"),
        ("score", "double"),
        ("tags", "array<long>"),
        ("weights", "array<double>"),
        ("payload", "binary"),
    ]


def _sample_row(Row):
    return Row(
        title="hello",
        count=7,
        score=-1.25,
        tags=[1, 2, 3],
        weights=[0.5, 1.5],
        payload=bytearray(b"hello-bytes"),
    )


def _check_pure_mode(Row, ArrayType, BinaryType, DoubleType, LongType, StringType, tf, dfutil):
    row = _sample_row(Row)
    serializer = dfutil.toTFExample(_sample_dtypes())
    records = serializer([row])

    _assert(len(records) == 1, "Expected one serialized record")
    _assert(records[0][1] is None, "Serialized TFRecord payload should use NullWritable")

    example = tf.train.Example()
    example.ParseFromString(bytes(records[0][0]))

    schema_no_hint = dfutil.infer_schema(example)
    schema_with_hint = dfutil.infer_schema(example, binary_features=["payload"])

    _assert(isinstance(schema_no_hint["payload"].dataType, StringType), "payload should default to StringType without a binary hint")
    _assert(isinstance(schema_with_hint["payload"].dataType, BinaryType), "payload should become BinaryType when hinted")
    _assert(isinstance(schema_with_hint["tags"].dataType, ArrayType), "tags should be an array")
    _assert(isinstance(schema_with_hint["weights"].dataType, ArrayType), "weights should be an array")
    _assert(isinstance(schema_with_hint["count"].dataType, LongType), "count should recover as LongType")
    _assert(isinstance(schema_with_hint["score"].dataType, DoubleType), "score should recover as DoubleType")

    plain = list(dfutil.fromTFExample(records))[0].asDict()
    hinted = list(dfutil.fromTFExample(records, binary_features=["payload"]))[0].asDict()

    _assert(plain["payload"] == "hello-bytes", "Without a binary hint, bytes should decode as UTF-8 text")
    _assert(hinted["payload"] == bytearray(b"hello-bytes"), "With a binary hint, bytes should remain raw bytes")
    _assert(plain["title"] == row["title"], "String field should round-trip")
    _assert(plain["count"] == row["count"], "Integer field should round-trip")
    _assert(plain["score"] == row["score"], "Float field should round-trip")
    _assert(plain["tags"] == row["tags"], "Array field should round-trip")
    _assert(plain["weights"] == row["weights"], "Float array should round-trip")

    unsupported_message = None
    try:
        bad_serializer = dfutil.toTFExample([("bad", "struct<foo:int>")])
        list(bad_serializer([Row(bad="x")]))
    except Exception as exc:
        unsupported_message = str(exc)

    _assert(unsupported_message is not None and "Unsupported dtype" in unsupported_message, "Unsupported dtypes should fail loudly")

    return {
        "mode": "pure",
        "binary_hint": "ok",
        "unsupported_dtype": "ok",
        "roundtrip": "ok",
    }


def _check_tfrecord_classes(spark):
    required_classes = [
        "org.tensorflow.hadoop.io.TFRecordFileInputFormat",
        "org.tensorflow.hadoop.io.TFRecordFileOutputFormat",
    ]
    results = {}
    jvm = spark.sparkContext._jvm
    for class_name in required_classes:
        try:
            jvm.java.lang.Class.forName(class_name)
        except Exception as exc:
            raise RuntimeError(
                f"Missing {class_name} on the Spark classpath. Add the TensorFlow Hadoop jar with --jar or equivalent Spark classpath settings."
            ) from exc
        results[class_name] = "ok"
    return results


def _classpath_from_jars(jars):
    return os.pathsep.join(part for part in jars.split(",") if part)


def _check_spark_mode(Row, SparkSession, ArrayType, BinaryType, DoubleType, LongType, StringType, StructField, StructType, dfutil, master, jar):
    builder = (
        SparkSession.builder
        .appName("tfos_tfrecord_schema_probe")
        .master(master)
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "1")
    )
    if jar:
        classpath = _classpath_from_jars(jar)
        builder = (
            builder
            .config("spark.jars", jar)
            .config("spark.driver.extraClassPath", classpath)
            .config("spark.executor.extraClassPath", classpath)
        )

    spark = None
    tmp_dir = None
    try:
        spark = builder.getOrCreate()
        class_status = _check_tfrecord_classes(spark)

        schema = StructType([
            StructField("title", StringType(), False),
            StructField("count", LongType(), False),
            StructField("score", DoubleType(), False),
            StructField("tags", ArrayType(LongType()), False),
            StructField("weights", ArrayType(DoubleType()), False),
            StructField("payload", BinaryType(), False),
        ])
        data = [(
            "hello",
            7,
            -1.25,
            [1, 2, 3],
            [0.5, 1.5],
            bytearray(b"hello-bytes"),
        )]
        df = spark.createDataFrame(data, schema=schema)

        tmp_dir = tempfile.mkdtemp(prefix="tfos-tfr-probe-")
        output_dir = os.path.join(tmp_dir, "records")
        dfutil.saveAsTFRecords(df, output_dir)
        loaded = dfutil.loadTFRecords(spark.sparkContext, output_dir, binary_features=["payload"])
        got = loaded.collect()[0].asDict(recursive=True)

        _assert(got["title"] == "hello", "Saved and loaded string field should match")
        _assert(got["count"] == 7, "Saved and loaded integer field should match")
        _assert(got["score"] == -1.25, "Saved and loaded floating-point field should match")
        _assert(got["tags"] == [1, 2, 3], "Saved and loaded integer array should match")
        _assert(got["weights"] == [0.5, 1.5], "Saved and loaded float array should match")
        _assert(got["payload"] == bytearray(b"hello-bytes"), "Saved and loaded binary field should match")

        return {
            "mode": "spark",
            "classpath": class_status,
            "roundtrip": "ok",
        }
    finally:
        if spark is not None:
            spark.stop()
        if tmp_dir is not None:
            shutil.rmtree(tmp_dir, ignore_errors=True)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Tiny smoke probe for TensorFlowOnSpark dfutil TFRecord helpers. "
            "Run the default pure mode for a safe local check, or add --mode spark "
            "with a TensorFlow Hadoop jar to verify Spark round-tripping too."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("pure", "spark", "all"),
        default="pure",
        help="Select the amount of validation to run.",
    )
    parser.add_argument(
        "--master",
        default="local[1]",
        help="Spark master to use for Spark-mode checks.",
    )
    parser.add_argument(
        "--jar",
        default=None,
        help="Optional TensorFlow Hadoop jar to add to the Spark classpath.",
    )
    args = parser.parse_args(argv)

    try:
        runtime = _runtime_modules()
        summary = {"mode": args.mode}

        if args.mode in ("pure", "all"):
            summary["pure"] = _check_pure_mode(
                runtime["Row"],
                runtime["ArrayType"],
                runtime["BinaryType"],
                runtime["DoubleType"],
                runtime["LongType"],
                runtime["StringType"],
                runtime["tf"],
                runtime["dfutil"],
            )

        if args.mode in ("spark", "all"):
            try:
                from pyspark.sql import SparkSession
            except Exception as exc:  # pragma: no cover - environment guard
                raise RuntimeError("PySpark is required for Spark-mode checks.") from exc

            summary["spark"] = _check_spark_mode(
                runtime["Row"],
                SparkSession,
                runtime["ArrayType"],
                runtime["BinaryType"],
                runtime["DoubleType"],
                runtime["LongType"],
                runtime["StringType"],
                runtime["StructField"],
                runtime["StructType"],
                runtime["dfutil"],
                args.master,
                args.jar,
            )

        print(json.dumps(summary, sort_keys=True, default=str))
        return 0
    except Exception as exc:
        print(f"tfos_tfrecord_schema_probe: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
