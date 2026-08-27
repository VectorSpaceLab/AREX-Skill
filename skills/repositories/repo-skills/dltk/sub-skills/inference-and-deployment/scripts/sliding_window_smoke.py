#!/usr/bin/env python
"""Run a deterministic, model-free smoke for DLTK sliding-window assembly.

Run this command from the `inference-and-deployment/` sub-skill directory:
    python scripts/sliding_window_smoke.py

The first case uses DLTK's native test geometry. The second case exercises a
smaller output patch, explicit overlap, and batch_size > 1. No TensorFlow
graph, data file, network, or model export is loaded. The installed dltk.utils
implementation is used when available; a small DLTK-compatible fallback keeps
this check self-contained.
"""
from __future__ import print_function

import argparse
import sys

import numpy as np


class _Shape(object):
    def __init__(self, values):
        self._values = tuple(values)

    def as_list(self):
        return list(self._values)


class _Tensor(object):
    def __init__(self, shape):
        self._shape = tuple(shape)

    def get_shape(self):
        return _Shape(self._shape)


class _Session(object):
    """Return constant ones with the requested op's non-batch shape."""
    def run(self, ops, feed_dict):
        feed_value = next(iter(feed_dict.values()))
        batch = feed_value.shape[0]
        return [np.ones((batch,) + tuple(op.get_shape().as_list()[1:]),
                         dtype=np.float32) for op in ops]


class _SliceFriendlyArray(np.ndarray):
    """Permit the list-of-slices indexing used by this historical helper."""
    def __new__(cls, value):
        return np.asarray(value).view(cls)

    def __array_finalize__(self, value):
        del value

    @staticmethod
    def _key(key):
        return tuple(key) if isinstance(key, list) else key

    def __getitem__(self, key):
        return super(_SliceFriendlyArray, self).__getitem__(self._key(key))

    def __setitem__(self, key, value):
        return super(_SliceFriendlyArray, self).__setitem__(self._key(key), value)


class _NumpyProxy(object):
    """Keep the compatibility shim local to this smoke process."""
    def __init__(self, module):
        self._module = module

    def zeros(self, *args, **kwargs):
        return _SliceFriendlyArray(self._module.zeros(*args, **kwargs))

    def zeros_like(self, *args, **kwargs):
        return _SliceFriendlyArray(self._module.zeros_like(*args, **kwargs))

    def pad(self, *args, **kwargs):
        return _SliceFriendlyArray(self._module.pad(*args, **kwargs))

    def __getattr__(self, name):
        return getattr(self._module, name)


def _local_sliding_window(img_shape, window_shape, has_batch_dim=True, striding=None):
    """DLTK-compatible iterator used only if dltk is not importable."""
    class SlidingWindow(object):
        def __init__(self, image_shape, patch_shape, batch_dim, step):
            self.img_shape = image_shape
            self.window_shape = patch_shape
            self.rank = len(image_shape)
            self.curr_pos = [0] * self.rank
            self.end_pos = [0] * self.rank
            self.done = False
            self.striding = patch_shape if step is None else step
            self.has_batch_dim = batch_dim

        def __iter__(self):
            return self

        def __next__(self):
            if self.done:
                raise StopIteration()
            slicer = ([slice(None)] * (self.rank + 1)
                      if self.has_batch_dim else [slice(None)] * self.rank)
            move_dim = True
            for dim, pos in enumerate(self.curr_pos):
                low = pos
                high = pos + self.window_shape[dim]
                if move_dim:
                    if high >= self.img_shape[dim]:
                        self.curr_pos[dim] = 0
                        move_dim = True
                    else:
                        self.curr_pos[dim] += self.striding[dim]
                        move_dim = False
                if high >= self.img_shape[dim]:
                    low = self.img_shape[dim] - self.window_shape[dim]
                    high = self.img_shape[dim]
                slicer[dim + 1 if self.has_batch_dim else dim] = slice(low, high)
            if (np.array(self.curr_pos) == self.end_pos).all():
                self.done = True
            return slicer

        next = __next__

    return SlidingWindow(img_shape, window_shape, has_batch_dim, striding)


def _local_inference(session, ops_list, sample_dict, batch_size=1, striding=None):
    """A no-dependency copy of the public helper's assembly semantics."""
    assert batch_size > 0, 'Batch size has to be 1 or bigger'
    placeholder = list(sample_dict.keys())[0]
    pl_shape = placeholder.get_shape().as_list()
    pl_bshape = pl_shape[1:-1]
    inp_shape = list(list(sample_dict.values())[0].shape)
    inp_bshape = inp_shape[1:-1]
    out_dummies = [np.zeros(
        [inp_shape[0]] + inp_bshape + [op.get_shape().as_list()[-1]]
        if len(op.get_shape().as_list()) == len(inp_shape) else [])
        for op in ops_list]
    out_dummy_counter = [np.zeros_like(output) for output in out_dummies]
    op_shape = ops_list[0].get_shape().as_list()
    op_bshape = op_shape[1:-1]
    out_diff = np.array(pl_bshape) - np.array(op_bshape)
    padding = [[0, 0]] + [[diff // 2, diff - diff // 2] for diff in out_diff] + [[0, 0]]
    padded_dict = {key: np.pad(value, padding, mode='constant')
                   for key, value in sample_dict.items()}
    f_bshape = list(list(padded_dict.values())[0].shape[1:-1])
    if not striding:
        striding = (list(np.maximum(1, np.array(op_bshape) // 2))
                    if all(out_diff == 0) else op_bshape)
    sw = _local_sliding_window(f_bshape, pl_bshape, True, striding)
    out_sw = _local_sliding_window(inp_bshape, op_bshape, True, striding)
    slicers, output_slicers = [], []
    done = False
    while True:
        try:
            slicer = next(sw)
            output_slicer = next(out_sw)
        except StopIteration:
            done = True
        if batch_size == 1:
            sw_dict = {key: value[tuple(slicer)] for key, value in padded_dict.items()}
            op_parts = session.run(ops_list, feed_dict=sw_dict)
            for index in range(len(op_parts)):
                out_dummies[index][tuple(output_slicer)] += op_parts[index]
                out_dummy_counter[index][tuple(output_slicer)] += 1
        else:
            slicers.append(slicer)
            output_slicers.append(output_slicer)
            if len(slicers) == batch_size or done:
                slices_dict = {key: np.concatenate(
                    [value[tuple(item)] for item in slicers], 0)
                    for key, value in padded_dict.items()}
                all_op_parts = session.run(ops_list, feed_dict=slices_dict)
                zipped_parts = zip(*[np.array_split(part, len(slicers))
                                     for part in all_op_parts])
                for output_slicer, op_parts in zip(output_slicers, zipped_parts):
                    for index in range(len(op_parts)):
                        out_dummies[index][tuple(output_slicer)] += op_parts[index]
                        out_dummy_counter[index][tuple(output_slicer)] += 1
                slicers, output_slicers = [], []
        if done:
            break
    return [output / counter for output, counter in
            zip(out_dummies, out_dummy_counter)]


def _get_inference():
    """Load the public package when installed, otherwise use the local check."""
    try:
        from dltk import utils
        return utils, True
    except ImportError:
        return None, False


def _run_one(inference, use_package, placeholder, op, sample, batch_size, striding=None):
    if not use_package:
        return _local_inference(_Session(), [op], {placeholder: sample}, batch_size, striding)[0]
    from dltk import utils
    original_numpy = utils.np
    utils.np = _NumpyProxy(np)
    try:
        return inference(_Session(), [op], {placeholder: sample}, batch_size, striding)[0]
    finally:
        utils.np = original_numpy


def run_smoke():
    utils, use_package = _get_inference()
    inference = utils.sliding_window_segmentation_inference if use_package else None

    # Native test shape: [batch, 1, 2, channels] op over [batch, 4, 4, channels].
    native_input = _Tensor([1, 1, 2, 1])
    native_op = _Tensor([1, 1, 2, 1])
    native_value = np.ones((1, 4, 4, 1), dtype=np.float32)
    native_result = _run_one(inference, use_package, native_input, native_op,
                             native_value, batch_size=1)
    if native_result.shape != native_value.shape or not np.array_equal(native_result, native_value):
        raise AssertionError('native-shaped constant assembly did not reproduce the input shape/value')

    # Difficult synthetic case: smaller output, overlap, and batched windows.
    small_input = _Tensor([None, 4, 4, 1])
    small_op = _Tensor([None, 2, 2, 2])
    small_value = np.ones((1, 6, 6, 1), dtype=np.float32)
    small_result = _run_one(inference, use_package, small_input, small_op,
                            small_value, batch_size=2, striding=[1, 1])
    expected_shape = (1, 6, 6, 2)
    if small_result.shape != expected_shape or not np.isfinite(small_result).all():
        raise AssertionError('smaller-output batched assembly returned {}'.format(small_result.shape))
    if not np.array_equal(small_result, np.ones(expected_shape, dtype=np.float32)):
        raise AssertionError('overlap averaging did not preserve the constant prediction')

    return use_package


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Run deterministic DLTK sliding-window smoke checks; no model or data is loaded.')
    parser.add_argument('--quiet', action='store_true',
                        help='print only the final status line')
    args = parser.parse_args(argv)
    used_package = run_smoke()
    if not args.quiet:
        print('native-shaped constant assembly: PASS')
        print('smaller-output + overlap + batch_size=2 assembly: PASS')
        print('package path: {}'.format('installed dltk.utils' if used_package else 'self-contained DLTK-compatible fallback'))
    print('sliding-window smoke: PASS')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (AssertionError, ImportError, ValueError) as error:
        print('sliding-window smoke: FAIL: {}'.format(error), file=sys.stderr)
        sys.exit(1)
