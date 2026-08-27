#!/usr/bin/env python3
"""Deterministic smoke checks for core einops tensor recipes.

This script is safe to run from any working directory once `einops` and `numpy`
are available. It avoids private repository paths and prints compact JSON-ish
summaries so future agents can inspect shapes quickly.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Callable


def _import_deps():
    try:
        import numpy as np
        from einops import asnumpy, parse_shape, rearrange, reduce, repeat
    except Exception as exc:  # pragma: no cover - help path only
        print(f"[shape_recipe_smoke] missing dependency: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    return np, asnumpy, parse_shape, rearrange, reduce, repeat


@dataclass(frozen=True)
class Case:
    name: str
    fn: Callable


def _summarize(label: str, array) -> str:
    shape = tuple(array.shape)
    dtype = str(array.dtype)
    flat = array.reshape(-1)
    sample = flat[: min(8, flat.size)].tolist()
    return json.dumps({"case": label, "shape": shape, "dtype": dtype, "sample": sample}, sort_keys=True)


def build_cases(np, asnumpy, parse_shape, rearrange, reduce, repeat):
    x = np.arange(2 * 3 * 4 * 5 * 6).reshape(2, 3, 4, 5, 6)
    image = np.arange(2 * 4 * 6 * 3).reshape(2, 4, 6, 3)
    video = np.arange(3 * 2 * 4 * 8 * 10).reshape(3, 2, 4, 8, 10)
    gray = np.arange(4 * 5).reshape(4, 5)

    def case_rearrange_transpose():
        y = rearrange(x, "a b c d e -> e d c b a")
        assert y.shape == (6, 5, 4, 3, 2)
        assert y[0, 0, 0, 0, 0] == x[0, 0, 0, 0, 0]
        return y

    def case_rearrange_flatten():
        y = rearrange(x, "a b c d e -> (a b c d e)")
        assert y.shape == (2 * 3 * 4 * 5 * 6,)
        assert y[0] == x.reshape(-1)[0]
        return y

    def case_rearrange_unflatten():
        flat = rearrange(image, "b h w c -> b (h w c)")
        shape = parse_shape(image, "b h w _")
        y = rearrange(flat, "b (h w c) -> b h w c", c=3, **shape)
        assert y.shape == image.shape
        assert np.array_equal(y, image)
        return y

    def case_reduce_pool():
        y = reduce(image, "b (h h2) (w w2) c -> b h w c", "max", h2=2, w2=3)
        assert y.shape == (2, 2, 2, 3)
        expected = image.reshape(2, 2, 2, 2, 3, 3).max(axis=(2, 4))
        assert np.array_equal(y, expected)
        return y

    def case_reduce_mean_keepdims():
        x_float = image.astype(np.float32)
        y = reduce(x_float, "b h w c -> b c 1 1", "mean")
        assert y.shape == (2, 3, 1, 1)
        expected = x_float.mean(axis=(1, 2), keepdims=True).transpose(0, 3, 1, 2)
        assert np.allclose(y, expected)
        return y

    def case_repeat_rgb():
        y = repeat(gray, "h w -> h w c", c=3)
        assert y.shape == (4, 5, 3)
        assert np.array_equal(y[..., 0], gray)
        assert np.array_equal(y[..., 1], gray)
        return y

    def case_repeat_upsample():
        y = repeat(gray, "h w -> (h h2) (w w2)", h2=2, w2=3)
        assert y.shape == (8, 15)
        assert np.array_equal(y[:2, :3], np.full((2, 3), gray[0, 0]))
        return y

    def case_list_stack():
        stacked = rearrange([gray, gray + 100], "b h w -> b h w")
        assert stacked.shape == (2, 4, 5)
        assert np.array_equal(stacked[1], gray + 100)
        return stacked

    def case_list_concat():
        wide = rearrange([gray, gray + 10], "b h w -> h (b w)")
        assert wide.shape == (4, 10)
        assert np.array_equal(wide[:, :5], gray)
        assert np.array_equal(wide[:, 5:], gray + 10)
        return wide

    def case_ellipsis():
        y = rearrange(video, "frames batch channels ... -> batch channels ... frames")
        assert y.shape == (2, 4, 8, 10, 3)
        assert y[0, 0, 0, 0, 0] == video[0, 0, 0, 0, 0]
        return y

    def case_reduce_repeat_interplay():
        image_float = image.astype(np.float32)
        reduced = reduce(image_float, "b (h h2) (w w2) c -> b h w c", "mean", h2=2, w2=3)
        restored = repeat(reduced, "b h w c -> b (h h2) (w w2) c", h2=2, w2=3)
        assert restored.shape == image.shape
        assert np.array_equal(reduce(restored, "b (h h2) (w w2) c -> b h w c", "mean", h2=2, w2=3), reduced)
        return restored

    def case_asnumpy():
        arr = asnumpy(rearrange(gray, "h w -> w h"))
        assert isinstance(arr, np.ndarray)
        assert arr.shape == (5, 4)
        assert np.array_equal(arr, gray.T)
        return arr

    def case_parse_shape():
        parsed = parse_shape(image, "batch height width _")
        assert parsed == {"batch": 2, "height": 4, "width": 6}
        return np.array([parsed["batch"], parsed["height"], parsed["width"]])

    def case_video_depth_to_space():
        y = rearrange(video, "frames batch (channels h2 w2) height width -> frames batch channels (height h2) (width w2)", h2=2, w2=2, channels=1)
        assert y.shape == (3, 2, 1, 16, 20)
        return y

    return [
        Case("rearrange_transpose", case_rearrange_transpose),
        Case("rearrange_flatten", case_rearrange_flatten),
        Case("rearrange_unflatten", case_rearrange_unflatten),
        Case("reduce_pool", case_reduce_pool),
        Case("reduce_mean_keepdims", case_reduce_mean_keepdims),
        Case("repeat_rgb", case_repeat_rgb),
        Case("repeat_upsample", case_repeat_upsample),
        Case("list_stack", case_list_stack),
        Case("list_concat", case_list_concat),
        Case("ellipsis", case_ellipsis),
        Case("reduce_repeat_interplay", case_reduce_repeat_interplay),
        Case("asnumpy", case_asnumpy),
        Case("parse_shape", case_parse_shape),
        Case("video_depth_to_space", case_video_depth_to_space),
    ]


def negative_checks(np, rearrange, reduce, repeat, parse_shape):
    x = np.arange(2 * 3 * 4 * 5).reshape(2, 3, 4, 5)

    checks = [
        ("rearrange_wrong_shape", lambda: rearrange(x, "b c h -> b h c"), "Wrong shape"),
        ("rearrange_identifier_only_one_side", lambda: rearrange(x, "b c h w -> b h w"), "Identifiers only on one side"),
        ("repeat_missing_size", lambda: repeat(x[0], "h w -> h w c"), "Specify sizes for new axes in repeat"),
        ("reduce_nonfloating_mean", lambda: reduce(x, "b c h w -> b c", "mean"), "reduce_mean is not available for non-floating tensors"),
        ("parse_shape_duplicate", lambda: parse_shape(x, "a a b c"), "duplicate"),
        ("parse_shape_invalid", lambda: parse_shape(x, "_bad axis rest last"), "Invalid axis identifier"),
    ]

    for name, fn, expected in checks:
        try:
            fn()
        except Exception as exc:
            text = str(exc)
            assert expected.lower() in text.lower(), (name, text)
        else:
            raise AssertionError(f"negative check {name} did not fail")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        default="all",
        choices=["all", "positive", "negative"],
        help="Run only the positive examples, only the failure checks, or both.",
    )
    args = parser.parse_args(argv)

    np, asnumpy, parse_shape, rearrange, reduce, repeat = _import_deps()
    cases = build_cases(np, asnumpy, parse_shape, rearrange, reduce, repeat)

    selected = []
    if args.case in ("all", "positive"):
        selected.extend(cases)
    if args.case in ("all", "negative"):
        selected.append(Case("negative_checks", lambda: negative_checks(np, rearrange, reduce, repeat, parse_shape)))

    print(json.dumps({"script": "shape_recipe_smoke", "selected": args.case, "cases": [c.name for c in selected]}, sort_keys=True))
    for case in selected:
        result = case.fn()
        if result is not None:
            print(_summarize(case.name, np.asarray(result)))
        else:
            print(json.dumps({"case": case.name, "status": "ok"}, sort_keys=True))

    print(json.dumps({"status": "ok", "count": len(selected)}, sort_keys=True))


if __name__ == "__main__":
    main()
