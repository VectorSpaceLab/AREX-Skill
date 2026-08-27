#!/usr/bin/env python3
"""Create Tencent ML-Images-style TFRecord shards from local image-list shards.

Adapted from the repository's TFRecord converter. It preserves the feature
schema (`width`, `height`, `image`, `label`, `name`) while adding safer argparse
booleans, output-directory creation, max-file limiting, and overwrite checks.

Requires TensorFlow 1.x or a compatible TensorFlow runtime with compat.v1 APIs.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

np = None


def require_numpy():
    global np
    if np is None:
        try:
            import numpy as numpy  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on runtime
            raise SystemExit(f"NumPy is required for TFRecord conversion: {exc}")
        np = numpy
    return np


def import_tensorflow():
    try:
        import tensorflow as tf  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on runtime
        raise SystemExit(f"TensorFlow is required for TFRecord conversion: {exc}")
    if hasattr(tf, "compat") and hasattr(tf.compat, "v1"):
        try:
            tf.compat.v1.disable_eager_execution()
        except Exception:
            pass
    return tf


def str2bool(value: str) -> bool:
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"expected boolean, got {value!r}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index-dir", "-idx", required=True, type=Path, help="Directory containing image-list shard text files.")
    parser.add_argument("--tfrecord-dir", "-tfs", required=True, type=Path, help="Output directory for .tfrecords shards.")
    parser.add_argument("--images-dir", "-im", required=True, type=Path, help="Root directory containing local images referenced by the list shards.")
    parser.add_argument("--num-classes", "-cls", required=True, type=int, help="Number of classes for one-hot multi-label output.")
    parser.add_argument("--one-hot", "-one", type=str2bool, default=True, help="true for dense float labels, false for scalar integer labels.")
    parser.add_argument("--start-index", "-sidx", type=int, default=0, help="Starting integer for output shard names.")
    parser.add_argument("--max-files", type=int, default=0, help="Maximum input shard files to process; 0 means all.")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing output .tfrecords file.")
    return parser.parse_args()


def int64_feature(tf, value):
    if not isinstance(value, list):
        value = [value]
    return tf.train.Feature(int64_list=tf.train.Int64List(value=value))


def bytes_feature(tf, value: bytes):
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def as_bytes(tf, value):
    compat = getattr(tf, "compat", None)
    if compat is not None and hasattr(compat, "as_bytes"):
        return compat.as_bytes(value)
    return value if isinstance(value, bytes) else str(value).encode("utf-8")


class ImageCoder:
    def __init__(self, tf):
        self.tf = tf
        v1 = getattr(getattr(tf, "compat", None), "v1", tf)
        self.sess = v1.Session()
        self.png_data = v1.placeholder(dtype=tf.string)
        image = tf.image.decode_png(self.png_data, channels=3)
        self.png_to_jpeg_op = tf.image.encode_jpeg(image, format="rgb", quality=100)
        self.jpeg_data = v1.placeholder(dtype=tf.string)
        self.decode_jpeg_op = tf.image.decode_jpeg(self.jpeg_data, channels=3)

    def png_to_jpeg(self, image_data: bytes) -> bytes:
        return self.sess.run(self.png_to_jpeg_op, feed_dict={self.png_data: image_data})

    def decode_jpeg(self, image_data: bytes):
        image = self.sess.run(self.decode_jpeg_op, feed_dict={self.jpeg_data: image_data})
        if len(image.shape) != 3 or image.shape[2] != 3:
            raise ValueError(f"expected RGB image, got shape {image.shape}")
        return image

    def close(self) -> None:
        self.sess.close()


def detect_image_kind(image_data: bytes) -> str:
    if image_data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if image_data.startswith(b"\xff\xd8"):
        return "jpeg"
    return "unknown"


def process_image(tf, filename: Path, coder: ImageCoder) -> Tuple[bytes, int, int]:
    image_data = filename.read_bytes()
    kind = detect_image_kind(image_data)
    if kind == "png":
        image_data = coder.png_to_jpeg(image_data)
    elif kind != "jpeg":
        # Some JPEG files lack a recognizable extension/header; try TensorFlow decode before failing.
        try:
            image = coder.decode_jpeg(image_data)
            return image_data, int(image.shape[0]), int(image.shape[1])
        except Exception as exc:
            raise ValueError(f"unsupported or corrupt image type {kind!r}: {exc}")
    image = coder.decode_jpeg(image_data)
    return image_data, int(image.shape[0]), int(image.shape[1])


def iter_shards(index_dir: Path, max_files: int) -> List[Path]:
    files = sorted(path for path in index_dir.iterdir() if path.is_file())
    if max_files:
        files = files[:max_files]
    if not files:
        raise SystemExit(f"No list shard files found in {index_dir}")
    return files


def parse_labels(parts: List[str], one_hot: bool, num_classes: int):
    numpy = require_numpy()
    if one_hot:
        label = numpy.zeros([num_classes], dtype=numpy.float32)
        for token in parts:
            class_part, _, conf_part = token.partition(":")
            class_id = int(class_part)
            if class_id < 0 or class_id >= num_classes:
                raise ValueError(f"class id {class_id} out of range for num_classes={num_classes}")
            label[class_id] = float(conf_part) if conf_part else 1.0
        return label
    if len(parts) != 1:
        raise ValueError("scalar-label mode expects exactly one label token")
    class_id = int(parts[0].split(":", 1)[0])
    if class_id < 0 or class_id >= num_classes:
        raise ValueError(f"class id {class_id} out of range for num_classes={num_classes}")
    return class_id


def write_shard(tf, shard_path: Path, output_path: Path, args: argparse.Namespace) -> int:
    writer_cls = getattr(getattr(tf, "python_io", None), "TFRecordWriter", None)
    if writer_cls is None:
        writer_cls = tf.io.TFRecordWriter
    coder = ImageCoder(tf)
    written = 0
    try:
        with writer_cls(str(output_path)) as writer, shard_path.open("r", encoding="utf-8", errors="replace") as rows:
            for lineno, raw in enumerate(rows, start=1):
                parts = raw.strip().split()
                if not parts:
                    continue
                image_name, label_tokens = parts[0], parts[1:]
                if not label_tokens:
                    raise ValueError(f"{shard_path}:{lineno}: missing labels")
                image_path = args.images_dir / image_name
                if not image_path.exists():
                    raise FileNotFoundError(f"{shard_path}:{lineno}: missing image {image_path}")
                image_data, height, width = process_image(tf, image_path, coder)
                label = parse_labels(label_tokens, args.one_hot, args.num_classes)
                if args.one_hot:
                    label_feature = bytes_feature(tf, as_bytes(tf, label.tobytes()))
                else:
                    label_feature = int64_feature(tf, int(label))
                example = tf.train.Example(features=tf.train.Features(feature={
                    "width": int64_feature(tf, width),
                    "height": int64_feature(tf, height),
                    "image": bytes_feature(tf, as_bytes(tf, image_data)),
                    "label": label_feature,
                    "name": bytes_feature(tf, as_bytes(tf, image_name)),
                }))
                writer.write(example.SerializeToString())
                written += 1
    finally:
        coder.close()
    return written


def main() -> int:
    args = parse_args()
    if args.num_classes <= 0:
        print("--num-classes must be positive", file=sys.stderr)
        return 2
    tf = import_tensorflow()
    args.tfrecord_dir.mkdir(parents=True, exist_ok=True)
    shards = iter_shards(args.index_dir, args.max_files)
    total = 0
    for offset, shard_path in enumerate(shards):
        output_path = args.tfrecord_dir / f"{args.start_index + offset}.tfrecords"
        if output_path.exists() and not args.overwrite:
            raise SystemExit(f"Refusing to overwrite existing output shard {output_path}; pass --overwrite if intentional")
        written = write_shard(tf, shard_path, output_path, args)
        total += written
        print(f"wrote {written} records -> {output_path}")
    print(f"finished {len(shards)} shard(s), {total} record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
