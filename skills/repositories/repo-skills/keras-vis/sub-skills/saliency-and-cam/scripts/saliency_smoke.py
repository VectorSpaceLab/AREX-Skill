#!/usr/bin/env python
"""Smoke-test keras-vis saliency and Grad-CAM workflows.

The script builds a tiny deterministic Keras model, runs saliency twice
(`keepdims=False` and `keepdims=True`), and runs Grad-CAM unless the user
chooses a dense-only model or disables CAM explicitly.

The smoke run is intentionally tiny and download-free. It prints output shapes
and value ranges so regressions in gradient flow, penultimate-layer selection,
or data-format handling are easy to spot.
"""
from __future__ import absolute_import, print_function

import argparse
import sys


def build_conv_model(input_shape, data_format):
    """Builds a small model with a spatial layer for CAM."""
    from keras.initializers import Constant
    from keras.layers import Dense, Flatten, Input
    from keras.layers.convolutional import Conv2D, MaxPooling2D
    from keras.models import Model

    inputs = Input(shape=input_shape, name='input')
    x = Conv2D(
        filters=2,
        kernel_size=(3, 3),
        padding='same',
        activation='relu',
        data_format=data_format,
        kernel_initializer=Constant(1.0),
        bias_initializer='zeros',
        name='conv',
    )(inputs)
    x = MaxPooling2D(pool_size=(2, 2), data_format=data_format, name='pool')(x)
    x = Flatten(name='flatten')(x)
    x = Dense(
        4,
        activation='relu',
        kernel_initializer=Constant(1.0),
        bias_initializer='zeros',
        name='hidden',
    )(x)
    outputs = Dense(
        1,
        activation='linear',
        kernel_initializer=Constant(1.0),
        bias_initializer='zeros',
        name='score',
    )(x)
    return Model(inputs, outputs, name='saliency_cam_smoke')


def build_dense_model(input_shape):
    """Builds a tiny model without any spatial layers."""
    from keras.initializers import Constant
    from keras.layers import Dense, Flatten, Input
    from keras.models import Model

    inputs = Input(shape=input_shape, name='input')
    x = Flatten(name='flatten')(inputs)
    x = Dense(
        4,
        activation='relu',
        kernel_initializer=Constant(1.0),
        bias_initializer='zeros',
        name='hidden',
    )(x)
    outputs = Dense(
        1,
        activation='linear',
        kernel_initializer=Constant(1.0),
        bias_initializer='zeros',
        name='score',
    )(x)
    return Model(inputs, outputs, name='saliency_only_smoke')


def build_seed_input(np, input_shape):
    """Creates a deterministic, centered seed input."""
    values = np.linspace(-1.0, 1.0, num=int(np.prod(input_shape)), dtype='float32')
    return values.reshape((1,) + tuple(input_shape))


def describe(name, array):
    """Prints the output shape and value range for a NumPy array."""
    print(
        '{}: shape={} range=[{:.6f}, {:.6f}]'.format(
            name,
            array.shape,
            float(array.min()),
            float(array.max()),
        )
    )


def parse_args(argv=None):
    """Parses CLI arguments for the smoke run."""
    parser = argparse.ArgumentParser(
        description='Smoke-test saliency and Grad-CAM on a tiny deterministic Keras model.'
    )
    parser.add_argument(
        '--dense-only',
        action='store_true',
        help='Build a dense-only model and skip CAM to exercise saliency-only behavior.',
    )
    parser.add_argument(
        '--no-cam',
        action='store_true',
        help='Skip the CAM run even if the model has a spatial layer.',
    )
    parser.add_argument(
        '--layer-idx',
        type=int,
        default=-1,
        help='Target layer index to visualize. Defaults to the final output layer.',
    )
    parser.add_argument(
        '--filter-index',
        type=int,
        default=0,
        help='Target output/filter index. Defaults to 0 for the smoke model.',
    )
    parser.add_argument(
        '--penultimate-layer-idx',
        type=int,
        default=None,
        help='Manual Grad-CAM penultimate-layer override. Defaults to auto-search.',
    )
    parser.add_argument(
        '--grad-modifier',
        choices=['absolute', 'relu', 'negate', 'small_values'],
        default='absolute',
        help='Gradient modifier to apply during saliency/CAM.',
    )
    parser.add_argument(
        '--backprop-modifier',
        choices=['guided', 'rectified', 'relu', 'deconv'],
        default=None,
        help='Optional backprop modifier for saliency/CAM.',
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    try:
        import numpy as np
        from keras import backend as K
        from vis.visualization import visualize_cam
        from vis.visualization import visualize_saliency
    except ImportError as exc:
        print('Import failed: {}'.format(exc), file=sys.stderr)
        print(
            'Use the legacy keras-vis stack with standalone Keras, TensorFlow 1.x-compatible graph mode, '
            'and the package dependencies required by this repo release.',
            file=sys.stderr,
        )
        return 2

    # Keep the smoke run small and graph-friendly. clear_session remains an
    # intentional graph reset, while the image format is restored for callers.
    old_format = K.image_data_format()
    try:
        K.clear_session()
        data_format = K.image_data_format()
        if data_format == 'channels_first':
            input_shape = (1, 4, 4)
        else:
            input_shape = (4, 4, 1)

        try:
            if args.dense_only:
                model = build_dense_model(input_shape)
            else:
                model = build_conv_model(input_shape, data_format)
        except ImportError as exc:
            print('Model construction import failed: {}'.format(exc), file=sys.stderr)
            print(
                'Install the standalone Keras layers package expected by keras-vis before running this smoke test.',
                file=sys.stderr,
            )
            return 2

        seed_input = build_seed_input(np, input_shape)

        print('model={} data_format={} input_shape={}'.format(model.name, data_format, input_shape))
        print(
            'saliency target: layer_idx={} filter_index={} grad_modifier={} backprop_modifier={}'.format(
                args.layer_idx,
                args.filter_index,
                args.grad_modifier,
                args.backprop_modifier,
            )
        )

        try:
            saliency = visualize_saliency(
                model,
                layer_idx=args.layer_idx,
                filter_indices=args.filter_index,
                seed_input=seed_input,
                backprop_modifier=args.backprop_modifier,
                grad_modifier=args.grad_modifier,
                keepdims=False,
            )
            saliency_keepdims = visualize_saliency(
                model,
                layer_idx=args.layer_idx,
                filter_indices=args.filter_index,
                seed_input=seed_input,
                backprop_modifier=args.backprop_modifier,
                grad_modifier=args.grad_modifier,
                keepdims=True,
            )
        except (ValueError, NotImplementedError) as exc:
            print('Saliency failed: {}'.format(exc), file=sys.stderr)
            print(
                'Check the target layer, filter index, and modifier values. For regression attention, '
                "'negate' shows decrease and 'small_values' shows maintenance. Use keepdims=True when the "
                'input is vector-like or when you need the full gradient tensor.',
                file=sys.stderr,
            )
            return 3

        describe('saliency', saliency)
        describe('saliency_keepdims', saliency_keepdims)

        if args.no_cam or args.dense_only:
            print('cam: skipped')
            return 0

        print('cam target: layer_idx={} penultimate_layer_idx={}'.format(args.layer_idx, args.penultimate_layer_idx))
        try:
            cam_kwargs = {}
            if args.penultimate_layer_idx is not None:
                cam_kwargs['penultimate_layer_idx'] = args.penultimate_layer_idx
            cam = visualize_cam(
                model,
                layer_idx=args.layer_idx,
                filter_indices=args.filter_index,
                seed_input=seed_input,
                backprop_modifier=args.backprop_modifier,
                grad_modifier=args.grad_modifier,
                **cam_kwargs
            )
        except (ValueError, NotImplementedError) as exc:
            print('CAM failed: {}'.format(exc), file=sys.stderr)
            print(
                'If Grad-CAM cannot find a penultimate Conv or Pooling layer, choose an earlier spatial layer '
                'with --penultimate-layer-idx or fall back to saliency. Guided/rectified backprop also requires '
                'the legacy TensorFlow graph-mode path.',
                file=sys.stderr,
            )
            return 4

        describe('cam', cam)
        return 0
    finally:
        K.set_image_data_format(old_format)

if __name__ == '__main__':
    sys.exit(main())
