#!/usr/bin/env python
"""Validate DLTK sliding-window geometry without a model, data, or network.

Run this command from the `inference-and-deployment/` sub-skill directory. The
shapes are spatial only (do not include batch or channels), for example:
    python scripts/sliding_window_plan.py --input-shape 8,8,8 \
        --window-shape 4,4,4 --output-shape 2,2,2 --batch-size 4
"""
from __future__ import print_function

import argparse
import sys


def _shape(text, option):
    try:
        values = tuple(int(part.strip()) for part in text.split(',') if part.strip())
    except ValueError:
        raise ValueError('{} must be comma-separated positive integers'.format(option))
    if not values or any(value <= 0 for value in values):
        raise ValueError('{} must contain positive integers'.format(option))
    return values


def _positions(image_dim, window_dim, stride):
    """Return the positions emitted by DLTK's iterator on one axis."""
    if image_dim < window_dim:
        raise ValueError(
            'window {} exceeds padded image {}; no valid window exists'.format(
                window_dim, image_dim))
    positions = []
    current = 0
    while True:
        high = current + window_dim
        positions.append(min(current, image_dim - window_dim))
        if high >= image_dim:
            current = 0
        else:
            current += stride
        if current == 0:
            break
    return positions


def make_plan(input_shape, window_shape, output_shape, stride=None, batch_size=1):
    """Validate geometry and return a source-semantic tile plan."""
    if not (len(input_shape) == len(window_shape) == len(output_shape)):
        raise ValueError('input, window, and output ranks must be equal; got {}, {}, {}'.format(
            len(input_shape), len(window_shape), len(output_shape)))
    if len(input_shape) == 0:
        raise ValueError('shapes must have at least one spatial dimension')
    if any(i < o for i, o in zip(input_shape, output_shape)):
        raise ValueError(
            'input dimensions must be >= output dimensions so the final volume is covered; '
            'got input={} output={}'.format(input_shape, output_shape))
    if any(w < o for w, o in zip(window_shape, output_shape)):
        raise ValueError(
            'window dimensions must be >= output dimensions for DLTK padding; '
            'got window={} output={}'.format(window_shape, output_shape))
    if batch_size <= 0:
        raise ValueError('batch-size must be a positive integer; got {}'.format(batch_size))

    diff = tuple(w - o for w, o in zip(window_shape, output_shape))
    padding = tuple((d // 2, d - d // 2) for d in diff)
    padded_shape = tuple(i + d for i, d in zip(input_shape, diff))
    if stride is None:
        stride = tuple(max(1, o // 2) for o in output_shape) \
            if all(d == 0 for d in diff) else output_shape
        stride_source = 'DLTK default'
    else:
        stride_source = 'explicit'
        if len(stride) != len(input_shape):
            raise ValueError('stride rank must equal shape rank; got {} and {}'.format(
                len(stride), len(input_shape)))
        if any(s <= 0 for s in stride):
            raise ValueError('stride values must be positive; got {}'.format(stride))
    if any(s > o for s, o in zip(stride, output_shape)):
        raise ValueError(
            'stride {} exceeds output tile {}; this can leave uncovered voxels and a '
            'zero division counter'.format(stride, output_shape))

    input_positions = tuple(_positions(p, w, s)
                            for p, w, s in zip(padded_shape, window_shape, stride))
    output_positions = tuple(_positions(i, o, s)
                             for i, o, s in zip(input_shape, output_shape, stride))
    tile_count = 1
    for positions in input_positions:
        tile_count *= len(positions)
    output_tile_count = 1
    for positions in output_positions:
        output_tile_count *= len(positions)
    if tile_count != output_tile_count:
        raise ValueError(
            'input and output iterators emit different tile counts ({} vs {}); '
            'check window/output/stride geometry'.format(tile_count, output_tile_count))
    calls = (tile_count + batch_size - 1) // batch_size
    return {
        'input_shape': input_shape,
        'window_shape': window_shape,
        'output_shape': output_shape,
        'diff': diff,
        'padding': padding,
        'padded_shape': padded_shape,
        'stride': tuple(stride),
        'stride_source': stride_source,
        'input_positions': input_positions,
        'output_positions': output_positions,
        'tile_count': tile_count,
        'session_calls': calls,
        'batch_size': batch_size,
    }


def _parser():
    parser = argparse.ArgumentParser(
        description='Validate DLTK sliding-window geometry and print a tile plan.')
    parser.add_argument('--input-shape', required=True,
                        help='spatial input volume, comma-separated (for example 128,128,64)')
    parser.add_argument('--window-shape', required=True,
                        help='spatial predictor input patch, comma-separated')
    parser.add_argument('--output-shape', required=True,
                        help='spatial predictor output patch, comma-separated')
    parser.add_argument('--stride', default=None,
                        help='optional positive spatial step, comma-separated')
    parser.add_argument('--batch-size', type=int, default=1,
                        help='windows per session call (default: 1)')
    return parser


def main(argv=None):
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        input_shape = _shape(args.input_shape, '--input-shape')
        window_shape = _shape(args.window_shape, '--window-shape')
        output_shape = _shape(args.output_shape, '--output-shape')
        stride = _shape(args.stride, '--stride') if args.stride is not None else None
        plan = make_plan(input_shape, window_shape, output_shape, stride, args.batch_size)
    except ValueError as error:
        parser.error(str(error))
    print('DLTK sliding-window plan (no model/data/network used)')
    print('  input spatial shape:  {}'.format(plan['input_shape']))
    print('  window spatial shape: {}'.format(plan['window_shape']))
    print('  output spatial shape: {}'.format(plan['output_shape']))
    print('  window-minus-output padding per side: {}'.format(plan['padding']))
    print('  padded input shape:    {}'.format(plan['padded_shape']))
    print('  stride ({}):           {}'.format(plan['stride_source'], plan['stride']))
    print('  input positions/axis:  {}'.format(
        tuple(len(p) for p in plan['input_positions'])))
    print('  output positions/axis: {}'.format(
        tuple(len(p) for p in plan['output_positions'])))
    print('  tiles: {}  batch_size: {}  session calls: {}'.format(
        plan['tile_count'], plan['batch_size'], plan['session_calls']))
    print('  coverage check:        PASS (every output axis is covered)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
