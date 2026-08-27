#!/usr/bin/env python3
"""Smoke-check MMCV media utilities without using the source checkout."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError('must be a positive integer')
    return parsed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            'Run deterministic MMCV media checks for image bytes, color order, '
            'resize scaling, normalization, array quantization, and optional '
            'optical-flow helpers.'
        )
    )
    parser.add_argument(
        '--skip-flow',
        action='store_true',
        help='Skip optical-flow helper checks.',
    )
    parser.add_argument(
        '--keep-temp',
        action='store_true',
        help='Keep the temporary directory and print its path.',
    )
    parser.add_argument(
        '--width',
        type=_positive_int,
        default=6,
        help='Width for the synthetic image before resizing (default: 6).',
    )
    parser.add_argument(
        '--height',
        type=_positive_int,
        default=4,
        help='Height for the synthetic image before resizing (default: 4).',
    )
    return parser


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _make_image(np, height: int, width: int):
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[..., 0] = np.arange(width, dtype=np.uint8)[None, :] * 3
    img[..., 1] = np.arange(height, dtype=np.uint8)[:, None] * 5
    img[..., 2] = 127
    return img


def _run_checks(args: argparse.Namespace, temp_dir: Path) -> list[str]:
    try:
        import numpy as np
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(f'numpy import failed: {exc}') from exc

    try:
        import mmcv
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(f'mmcv import failed: {exc}') from exc

    results: list[str] = []

    img_bgr = _make_image(np, args.height, args.width)
    image_path = temp_dir / 'synthetic.png'
    write_ok = mmcv.imwrite(img_bgr, str(image_path))
    _require(bool(write_ok), 'mmcv.imwrite returned false for synthetic PNG')
    _require(image_path.is_file(), 'synthetic image was not written')
    results.append('image-write')

    content = image_path.read_bytes()
    from_bytes_bgr = mmcv.imfrombytes(content, flag='color', channel_order='bgr')
    from_bytes_rgb = mmcv.imfrombytes(content, flag='color', channel_order='rgb')
    _require(from_bytes_bgr.shape == img_bgr.shape, 'imfrombytes BGR shape mismatch')
    _require(np.array_equal(from_bytes_rgb[..., ::-1], from_bytes_bgr), 'RGB/BGR channel conversion mismatch')
    results.append('image-bytes-color')

    read_passthrough = mmcv.imread(from_bytes_bgr)
    _require(read_passthrough is from_bytes_bgr, 'imread should return ndarray inputs unchanged')
    results.append('imread-array-passthrough')

    target_size = (args.width * 2, args.height * 3)
    resized, w_scale, h_scale = mmcv.imresize(from_bytes_bgr, target_size, return_scale=True)
    _require(resized.shape[:2] == (target_size[1], target_size[0]), 'imresize output shape does not match (height, width) expectation')
    _require(abs(w_scale - 2.0) < 1e-6, 'unexpected width scale from imresize')
    _require(abs(h_scale - 3.0) < 1e-6, 'unexpected height scale from imresize')
    results.append('resize-scale')

    multiple = mmcv.imresize_to_multiple(from_bytes_bgr, divisor=4, scale_factor=1.0)
    _require(multiple.shape[0] % 4 == 0 and multiple.shape[1] % 4 == 0, 'imresize_to_multiple did not produce multiples of divisor')
    padded = mmcv.impad(from_bytes_bgr, shape=(args.height + 2, args.width + 3), pad_val=(1, 2, 3))
    _require(padded.shape[:2] == (args.height + 2, args.width + 3), 'impad shape mismatch')
    results.append('resize-pad')

    mean = np.array([10, 20, 30], dtype=np.float32)
    std = np.array([2, 4, 5], dtype=np.float32)
    normalized = mmcv.imnormalize(from_bytes_bgr, mean, std, to_rgb=True)
    _require(normalized.dtype == np.float32, 'imnormalize should return float32')
    recovered = mmcv.imdenormalize(normalized, mean, std, to_bgr=True)
    _require(np.allclose(recovered, from_bytes_bgr.astype(np.float32), atol=1e-4), 'imdenormalize did not recover original values')
    results.append('normalize-denormalize')

    arr = np.array([-2.0, -1.0, -0.25, 0.25, 1.0, 2.0], dtype=np.float32)
    quantized = mmcv.quantize(arr, -1.0, 1.0, levels=16, dtype=np.uint8)
    dequantized = mmcv.dequantize(quantized, -1.0, 1.0, levels=16, dtype=np.float32)
    _require(quantized.dtype == np.uint8, 'quantize dtype mismatch')
    _require(dequantized.dtype == np.float32, 'dequantize dtype mismatch')
    _require(float(dequantized.min()) >= -1.0 and float(dequantized.max()) <= 1.0, 'dequantized values outside requested range')
    results.append('array-quantize')

    boxes = np.array([[0, 0, args.width - 1, args.height - 1]], dtype=np.float32)
    drawn = mmcv.imshow_bboxes(from_bytes_bgr, boxes, show=False, out_file=str(temp_dir / 'boxes.png'))
    _require(drawn.shape == from_bytes_bgr.shape, 'imshow_bboxes returned unexpected shape')
    _require((temp_dir / 'boxes.png').is_file(), 'imshow_bboxes did not write out_file')
    results.append('headless-bboxes')

    if not args.skip_flow:
        flow = np.zeros((args.height, args.width, 2), dtype=np.float32)
        flow[..., 0] = 0.5
        flow[..., 1] = -0.25
        flow_path = temp_dir / 'tiny.flo'
        mmcv.flowwrite(flow, str(flow_path))
        loaded_flow = mmcv.flowread(str(flow_path))
        _require(loaded_flow.shape == flow.shape, 'flowread shape mismatch')
        _require(np.allclose(loaded_flow, flow), 'uncompressed flow round-trip mismatch')
        dx, dy = mmcv.quantize_flow(flow, max_val=0.2, norm=True)
        recovered_flow = mmcv.dequantize_flow(dx, dy, max_val=0.2, denorm=True)
        _require(recovered_flow.shape == flow.shape, 'dequantize_flow shape mismatch')
        rgb = mmcv.flow2rgb(flow)
        _require(rgb.shape == flow.shape[:2] + (3,), 'flow2rgb shape mismatch')
        _require(np.isfinite(rgb).all(), 'flow2rgb produced non-finite values')
        results.append('flow-helpers')

    return results


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.keep_temp:
        temp_context = None
        temp_dir = Path(tempfile.mkdtemp(prefix='mmcv-media-smoke-'))
    else:
        temp_context = tempfile.TemporaryDirectory(prefix='mmcv-media-smoke-')
        temp_dir = Path(temp_context.name)

    try:
        results = _run_checks(args, temp_dir)
    except Exception as exc:
        print(f'FAILED: {exc}', file=sys.stderr)
        if args.keep_temp:
            print(f'temp_dir={temp_dir}', file=sys.stderr)
        return 1
    finally:
        if temp_context is not None:
            temp_context.cleanup()

    print('OK: ' + ', '.join(results))
    if args.keep_temp:
        print(f'temp_dir={temp_dir}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
