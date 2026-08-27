#!/usr/bin/env python3
"""Validate Tacotron train.txt rows and referenced NumPy spectrograms."""
import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, help="Directory containing train.txt and .npy files")
    parser.add_argument("--max-rows", type=int, default=0, help="Validate only the first N rows; 0 means all")
    args = parser.parse_args()
    if args.max_rows < 0:
        parser.error("--max-rows must be zero or positive")
    try:
        import numpy as np
    except ImportError:
        print("numpy is required for metadata validation", file=sys.stderr)
        return 2
    data_dir = os.path.abspath(args.data_dir)
    metadata = os.path.join(data_dir, "train.txt")
    if not os.path.isfile(metadata):
        print("missing train.txt: %s" % metadata, file=sys.stderr)
        return 1
    errors = []
    count = 0
    root = os.path.realpath(data_dir)
    with open(metadata, encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, 1):
            if args.max_rows and count >= args.max_rows:
                break
            count += 1
            line = raw.rstrip("\n")
            parts = line.split("|", 3)
            if len(parts) != 4:
                errors.append("line %d: expected 4 fields" % line_no)
                continue
            linear, mel, frames, text = parts
            try:
                frame_count = int(frames)
            except ValueError:
                errors.append("line %d: n_frames is not an integer" % line_no)
                continue
            if frame_count <= 0:
                errors.append("line %d: n_frames must be positive" % line_no)
                continue
            paths = []
            unsafe = False
            for name in (linear, mel):
                if not name or os.path.isabs(name):
                    unsafe = True
                    break
                path = os.path.realpath(os.path.join(data_dir, name))
                if os.path.commonpath((root, path)) != root:
                    unsafe = True
                    break
                paths.append(path)
            if unsafe:
                errors.append("line %d: array path must stay under data directory" % line_no)
                continue
            if any(not os.path.isfile(path) for path in paths):
                errors.append("line %d: referenced array missing" % line_no)
                continue
            try:
                linear_arr, mel_arr = (np.load(path, allow_pickle=False) for path in paths)
            except Exception as exc:  # diagnostic helper: report malformed arrays
                errors.append("line %d: cannot load array: %s" % (line_no, exc))
                continue
            if linear_arr.ndim != 2 or mel_arr.ndim != 2:
                errors.append("line %d: arrays must be rank 2" % line_no)
            if linear_arr.dtype != np.float32 or mel_arr.dtype != np.float32:
                errors.append("line %d: arrays must have float32 dtype" % line_no)
            if linear_arr.shape[0] != frame_count or mel_arr.shape[0] != frame_count:
                errors.append("line %d: metadata frame count does not match arrays" % line_no)
            if mel_arr.ndim == 2 and mel_arr.shape[1] != 80:
                errors.append("line %d: expected 80 mel columns, got %d" % (line_no, mel_arr.shape[1]))
            if linear_arr.ndim == 2 and linear_arr.shape[1] != 1025:
                errors.append("line %d: expected 1025 linear columns, got %d" % (line_no, linear_arr.shape[1]))
            if not text.strip():
                errors.append("line %d: text is empty" % line_no)
    if count == 0:
        errors.append("train.txt contains no rows")
    if errors:
        print("INVALID (%d checked rows)" % count)
        for error in errors:
            print("-", error)
        return 1
    print("VALID: %d rows" % count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
