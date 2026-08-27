#!/usr/bin/env python3
"""Deterministic NumPy smoke checks for einops.pack and einops.unpack.

The cases are adapted from public einops packing behavior: trivial stack and
concatenate replacements, heterogeneous round trips, class-token/multimodal
flows with zero-length tensors, manual multi-output unpacking, auto-batching,
`-1` inference, and expected packing errors. The script depends only on NumPy
and an installed einops package.
"""

from __future__ import annotations

import argparse
import sys
from typing import Callable, Iterable, Sequence


def _import_runtime():
    try:
        import numpy as np  # type: ignore
        from einops import pack, unpack  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - environment dependent
        missing = exc.name or "required package"
        print(
            f"Missing dependency {missing!r}. Install NumPy and einops, then rerun this script.",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    return np, pack, unpack


def _expect_error(fn: Callable[[], object], fragments: Iterable[str], label: str) -> None:
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - smoke script checks public error text
        message = str(exc)
        missing = [fragment for fragment in fragments if fragment not in message]
        if missing:
            raise AssertionError(
                f"{label}: expected fragments {missing!r} in {type(exc).__name__}: {message!r}"
            ) from exc
        return
    raise AssertionError(f"{label}: expected an exception")


def _assert_list_allclose(np, actual: Sequence[object], expected: Sequence[object]) -> None:
    assert len(actual) == len(expected)
    for got, want in zip(actual, expected):
        assert got.shape == want.shape
        np.testing.assert_allclose(got, want)


def case_trivial(verbose: bool = False) -> None:
    np, pack, _unpack = _import_runtime()
    height, width = 4, 5
    r = np.arange(height * width, dtype="float32").reshape(height, width)
    g = r + 100
    b = r + 200
    embeddings = np.arange(height * width * 3, dtype="float32").reshape(height, width, 3) + 300

    packed, ps = pack([r, g, b], "height width *")
    np.testing.assert_allclose(packed, np.stack([r, g, b], axis=2))
    assert ps == [(), (), ()]

    packed, _ = pack([r, g, b], "height * width")
    np.testing.assert_allclose(packed, np.stack([r, g, b], axis=1))

    packed, _ = pack([r, g, b], "* height width")
    np.testing.assert_allclose(packed, np.stack([r, g, b], axis=0))

    packed, _ = pack([r, g, b], "height *")
    np.testing.assert_allclose(packed, np.concatenate([r, g, b], axis=1))

    packed, _ = pack([r, g, b], "* width")
    np.testing.assert_allclose(packed, np.concatenate([r, g, b], axis=0))

    packed, ps = pack([r, g, b, embeddings], "height width *")
    expected = np.concatenate([r[:, :, None], g[:, :, None], b[:, :, None], embeddings], axis=2)
    np.testing.assert_allclose(packed, expected)
    assert ps == [(), (), (), (3,)]
    if verbose:
        print("trivial stack/concat packing ok")


def case_roundtrip(verbose: bool = False) -> None:
    np, pack, unpack = _import_runtime()
    a = np.arange(2 * 3 * 5, dtype="float32").reshape(2, 3, 5)
    b = np.arange(2 * 3 * 7 * 5, dtype="float32").reshape(2, 3, 7, 5) + 1000
    c = np.arange(2 * 3 * 7 * 9 * 5, dtype="float32").reshape(2, 3, 7, 9, 5) + 2000
    inputs = [a, b, c]

    packed, ps = pack(inputs, "i j * k")
    assert packed.shape == (2, 3, 71, 5)
    assert ps == [(), (7,), (7, 9)]
    recovered = unpack(packed, ps, "i j * k")
    _assert_list_allclose(np, recovered, inputs)

    repacked, ps2 = pack(recovered, "i j * k")
    assert ps2 == ps
    np.testing.assert_allclose(repacked, packed)
    if verbose:
        print("heterogeneous pack/unpack round trip ok")


def case_class_token_and_zero_length(verbose: bool = False) -> None:
    np, pack, unpack = _import_runtime()
    batch, height, width, channel = 2, 2, 3, 4
    class_token = np.arange(batch * channel, dtype="float32").reshape(batch, channel)
    image_tokens = np.arange(batch * height * width * channel, dtype="float32").reshape(
        batch, height, width, channel
    )
    text_tokens = np.zeros((batch, 0, channel), dtype="float32")

    packed, ps = pack([class_token, image_tokens, text_tokens], "batch * channel")
    assert packed.shape == (batch, 1 + height * width + 0, channel)
    assert ps == [(), (height, width), (0,)]

    processed = packed * 2 + 1
    class_out, image_out, text_out = unpack(processed, ps, "batch * channel_out")
    np.testing.assert_allclose(class_out, class_token * 2 + 1)
    np.testing.assert_allclose(image_out, image_tokens * 2 + 1)
    assert text_out.shape == (batch, 0, channel)
    if verbose:
        print("class token and zero-length modality packing ok")


def case_multi_output(verbose: bool = False) -> None:
    np, pack, unpack = _import_runtime()
    batch, height, width, mask_h, mask_w, classes = 2, 3, 4, 2, 3, 5
    feature_width = 5 + mask_h * mask_w + classes
    model_output = np.arange(batch * height * width * feature_width, dtype="float32").reshape(
        batch, height, width, feature_width
    )

    outputs = unpack(
        model_output,
        [[], [], [], [], [], [mask_h, mask_w], [classes]],
        "batch height width *",
    )
    assert [out.shape for out in outputs[:5]] == [(batch, height, width)] * 5
    assert outputs[5].shape == (batch, height, width, mask_h, mask_w)
    assert outputs[6].shape == (batch, height, width, classes)

    repacked, ps = pack(outputs, "batch height width *")
    assert ps == [(), (), (), (), (), (mask_h, mask_w), (classes,)]
    np.testing.assert_allclose(repacked, model_output)
    if verbose:
        print("manual multi-output unpacking ok")


def case_auto_batch(verbose: bool = False) -> None:
    np, pack, unpack = _import_runtime()
    height, width, channel = 3, 4, 2

    def image_classifier(images_bhwc):
        assert images_bhwc.ndim == 4
        return images_bhwc.mean(axis=(1, 2))

    def universal_predict(x):
        images_bhwc, ps = pack([x], "* height width channel")
        predictions = image_classifier(images_bhwc)
        [restored] = unpack(predictions, ps, "* cls")
        return restored, ps

    single = np.arange(height * width * channel, dtype="float32").reshape(height, width, channel)
    single_pred, single_ps = universal_predict(single)
    assert single_ps == [()]
    assert single_pred.shape == (channel,)
    np.testing.assert_allclose(single_pred, single.mean(axis=(0, 1)))

    batch = np.stack([single, single + 100], axis=0)
    batch_pred, batch_ps = universal_predict(batch)
    assert batch_ps == [(2,)]
    assert batch_pred.shape == (2, channel)
    np.testing.assert_allclose(batch_pred, batch.mean(axis=(1, 2)))
    if verbose:
        print("auto-batching pack/unpack ok")


def case_inference_and_errors(verbose: bool = False) -> None:
    np, pack, unpack = _import_runtime()
    x = np.arange(5, dtype="float32")

    parts = unpack(x, [[2], [1], [-1]], "*")
    assert [part.shape for part in parts] == [(2,), (1,), (2,)]
    np.testing.assert_allclose(np.concatenate(parts), x)

    parts = unpack(x, [[2], [3], [-1]], "*")
    assert [part.shape for part in parts] == [(2,), (3,), (0,)]

    nested = unpack(x, [[2, -1], [1, 5]], "*")
    assert nested[0].shape == (2, 0)
    assert nested[1].shape == (1, 5)

    _expect_error(lambda: pack([np.zeros((2, 3))], "height width"), ["No *-axis"], "missing star")
    _expect_error(
        lambda: pack([np.zeros((2, 3))], "height * *"),
        ["Duplicates in axes names"],
        "duplicate star",
    )
    _expect_error(
        lambda: pack([np.zeros((2, 3))], "height height *"),
        ["Duplicates in axes names"],
        "duplicate axis",
    )
    _expect_error(
        lambda: unpack(x, [[-1], [1], [-1]], "*"),
        ["more than one -1"],
        "too many inferred shapes",
    )
    _expect_error(
        lambda: unpack(x, [[2], [1], [1]], "*"),
        ["could not split axis"],
        "bad packed shapes",
    )
    if verbose:
        print("-1 inference and expected packing errors ok")


def run(case: str, verbose: bool = False) -> None:
    cases = {
        "trivial": case_trivial,
        "roundtrip": case_roundtrip,
        "class-zero": case_class_token_and_zero_length,
        "multi-output": case_multi_output,
        "auto-batch": case_auto_batch,
        "inference-errors": case_inference_and_errors,
    }
    selected = cases.keys() if case == "all" else [case]
    for name in selected:
        cases[name](verbose=verbose)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run deterministic smoke checks for einops.pack/unpack.")
    parser.add_argument(
        "--case",
        choices=["all", "trivial", "roundtrip", "class-zero", "multi-output", "auto-batch", "inference-errors"],
        default="all",
        help="Subset of smoke checks to run (default: all).",
    )
    parser.add_argument("--verbose", action="store_true", help="Print each successful case.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run(args.case, verbose=args.verbose)
    print(f"packing smoke passed: {args.case}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
