#!/usr/bin/env python
"""Bounded TensorFlow 1.x graph smoke checks for DLTK 0.2.1 networks.

This script constructs and executes tiny rank-5 graphs only. It does not read
medical data, download anything, train, export, create checkpoints, or write
files. Run it from any working directory after installing DLTK and its
verified TensorFlow 1.15.0 environment.
"""
from __future__ import print_function

import argparse
import os
import sys


FAMILIES = (
    'core', 'resnet', 'unet', 'fcn', 'deepmedic', 'autoencoder', 'gan',
    'super-resolution', 'all')


def _parser():
    parser = argparse.ArgumentParser(
        description='Build and run tiny DLTK TensorFlow 1.x network graphs; '
                    'no data, downloads, training, or checkpoint writes.')
    parser.add_argument(
        '--family', choices=FAMILIES, default='all',
        help='family to check (default: all; deepmedic uses an explicit tiny '
             'configuration rather than its large defaults)')
    return parser


def _finite(value):
    # All smoke outputs are numeric tensors. This also handles integer y_ and
    # pred tensors without adding a dependency beyond NumPy.
    import numpy as np
    return bool(np.all(np.isfinite(value)))


def _check_case(tf, np, name, inputs, outputs, expected_shapes):
    """Initialize, execute, and validate one graph case."""
    if not isinstance(inputs, (tuple, list)):
        inputs = [inputs]
    expected_keys = set(expected_shapes)
    if set(outputs) != expected_keys:
        raise AssertionError(
            '{} keys {} != expected {}'.format(
                name, sorted(outputs), sorted(expected_keys)))

    feed = {}
    for index, tensor in enumerate(inputs):
        shape = tensor.get_shape().as_list()
        feed[tensor] = np.random.RandomState(100 + index).normal(
            size=shape).astype(np.float32)

    init = tf.global_variables_initializer()
    config = tf.ConfigProto(
        intra_op_parallelism_threads=1, inter_op_parallelism_threads=1)
    with tf.Session(config=config) as session:
        session.run(init)
        values = session.run(outputs, feed_dict=feed)

    for key, value in values.items():
        actual = list(value.shape)
        expected = list(expected_shapes[key])
        if actual != expected:
            raise AssertionError(
                '{}[{}] shape {} != expected {}'.format(
                    name, key, actual, expected))
        if not _finite(value):
            raise AssertionError('{}[{}] contains non-finite values'.format(
                name, key))
    print('PASS {:12s} {}'.format(name, ', '.join(
        '{}={}'.format(key, list(values[key].shape))
        for key in sorted(values))))


def _core(tf, np):
    tf.reset_default_graph()
    tf.set_random_seed(7)
    inputs = tf.placeholder(tf.float32, [1, 4, 4, 4, 2], name='x')
    from dltk.core.activations import leaky_relu
    from dltk.core.residual_unit import vanilla_residual_unit_3d
    from dltk.core.upsample import linear_upsample_3d
    with tf.variable_scope('residual'):
        residual = vanilla_residual_unit_3d(
            inputs, out_filters=2, strides=(1, 1, 1),
            mode=tf.estimator.ModeKeys.EVAL)
    with tf.variable_scope('upsample'):
        upsample = linear_upsample_3d(inputs, strides=(2, 2, 2))
    outputs = {'residual': residual, 'upsample': upsample,
               'activation': leaky_relu(tf.constant([-1., 1.]), 0.1)}
    _check_case(tf, np, 'core', inputs, outputs, {
        'residual': (1, 4, 4, 4, 2),
        'upsample': (1, 8, 8, 8, 2),
        'activation': (2,)})


def _resnet(tf, np):
    tf.reset_default_graph()
    tf.set_random_seed(7)
    inputs = tf.placeholder(tf.float32, [1, 4, 4, 4, 1], name='x')
    from dltk.networks.regression_classification.resnet import resnet_3d
    outputs = resnet_3d(
        inputs, num_classes=3, num_res_units=1,
        filters=(2, 4), strides=((1, 1, 1), (1, 1, 1)),
        mode=tf.estimator.ModeKeys.EVAL)
    _check_case(tf, np, 'resnet', inputs, outputs, {
        'logits': (1, 3), 'y_prob': (1, 3), 'y_': (1,)})


def _unet(tf, np):
    tf.reset_default_graph()
    tf.set_random_seed(7)
    inputs = tf.placeholder(tf.float32, [1, 4, 4, 4, 1], name='x')
    from dltk.networks.segmentation.unet import residual_unet_3d
    outputs = residual_unet_3d(
        inputs, num_classes=3, num_res_units=1,
        filters=(2, 4), strides=((1, 1, 1), (1, 1, 1)),
        mode=tf.estimator.ModeKeys.EVAL)
    _check_case(tf, np, 'unet', inputs, outputs, {
        'logits': (1, 4, 4, 4, 3),
        'y_prob': (1, 4, 4, 4, 3),
        'y_': (1, 4, 4, 4)})


def _fcn(tf, np):
    tf.reset_default_graph()
    tf.set_random_seed(7)
    inputs = tf.placeholder(tf.float32, [1, 4, 4, 4, 1], name='x')
    from dltk.networks.segmentation.fcn import residual_fcn_3d
    outputs = residual_fcn_3d(
        inputs, num_classes=3, num_res_units=1,
        filters=(2, 4), strides=((1, 1, 1), (1, 1, 1)),
        mode=tf.estimator.ModeKeys.EVAL)
    _check_case(tf, np, 'fcn', inputs, outputs, {
        'logits': (1, 4, 4, 4, 3),
        'y_prob': (1, 4, 4, 4, 3),
        'y_': (1, 4, 4, 4)})


def _deepmedic(tf, np):
    """Use a tiny single-path configuration; never use the large defaults."""
    tf.reset_default_graph()
    tf.set_random_seed(7)
    inputs = tf.placeholder(tf.float32, [1, 3, 3, 3, 1], name='x')
    from dltk.networks.segmentation.deepmedic import deepmedic_3d
    outputs = deepmedic_3d(
        inputs, num_classes=2,
        normal_filters=(2,), normal_strides=((1, 1, 1),),
        normal_kernels=((1, 1, 1),), normal_residuals=(),
        normal_input_shape=(3, 3, 3),
        subsampled_filters=(), subsampled_strides=(),
        subsampled_kernels=(), subsampled_residuals=(),
        subsampled_input_shapes=(), subsample_factors=(),
        fc_filters=(2,), first_fc_kernel=(1, 1, 1), fc_residuals=(),
        padding='SAME', use_prelu=False,
        mode=tf.estimator.ModeKeys.EVAL, use_bias=True)
    _check_case(tf, np, 'deepmedic', inputs, outputs, {
        'logits': (1, 3, 3, 3, 2),
        'y_prob': (1, 3, 3, 3, 2),
        'y_': (1, 3, 3, 3)})


def _autoencoder(tf, np):
    tf.reset_default_graph()
    tf.set_random_seed(7)
    inputs = tf.placeholder(tf.float32, [1, 4, 4, 4, 1], name='x')
    from dltk.networks.autoencoder.convolutional_autoencoder import (
        convolutional_autoencoder_3d)
    outputs = convolutional_autoencoder_3d(
        inputs, num_convolutions=1, num_hidden_units=3, filters=(2,),
        strides=((1, 1, 1),), mode=tf.estimator.ModeKeys.EVAL)
    _check_case(tf, np, 'autoencoder', inputs, outputs, {
        'hidden_units': (1, 3), 'x_': (1, 4, 4, 4, 1)})


def _gan(tf, np):
    tf.reset_default_graph()
    tf.set_random_seed(7)
    gen_input = tf.placeholder(tf.float32, [1, 1, 1, 1, 2], name='noise')
    disc_input = tf.placeholder(tf.float32, [1, 2, 2, 2, 1], name='image')
    from dltk.networks.gan.dcgan import (dcgan_discriminator_3d,
                                          dcgan_generator_3d)
    with tf.variable_scope('generator'):
        generated = dcgan_generator_3d(
            gen_input, filters=(2,), kernel_size=((1, 1, 1),),
            strides=((1, 1, 1),), mode=tf.estimator.ModeKeys.EVAL)
    with tf.variable_scope('discriminator'):
        discriminated = dcgan_discriminator_3d(
            disc_input, filters=(2,), strides=((1, 1, 1),),
            mode=tf.estimator.ModeKeys.EVAL)
    outputs = dict(generated)
    outputs.update(discriminated)
    _check_case(tf, np, 'gan', [gen_input, disc_input], outputs, {
        'gen': (1, 1, 1, 1, 2),
        'logits': (1, 1), 'probs': (1, 1), 'pred': (1, 1)})


def _super_resolution(tf, np):
    tf.reset_default_graph()
    tf.set_random_seed(7)
    inputs = tf.placeholder(tf.float32, [1, 2, 2, 2, 1], name='low_resolution')
    from dltk.networks.super_resolution.simple_super_resolution import (
        simple_super_resolution_3d)
    outputs = simple_super_resolution_3d(
        inputs, num_convolutions=1, filters=(2,),
        upsampling_factor=(2, 2, 2), mode=tf.estimator.ModeKeys.EVAL)
    _check_case(tf, np, 'super-resolution', inputs, outputs, {
        'x_': (1, 4, 4, 4, 1)})


def main(argv=None):
    args = _parser().parse_args(argv)
    # Keep TensorFlow's legacy import quiet and force the tiny check to CPU.
    # This avoids reserving accelerator memory and does not require a device.
    os.environ.setdefault('CUDA_VISIBLE_DEVICES', '')
    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
    try:
        import numpy as np
        import tensorflow as tf
    except ImportError as exc:
        print('ERROR: this check needs the prepared DLTK/TensorFlow 1.x '
              'environment: {}'.format(exc), file=sys.stderr)
        return 2

    if not str(tf.__version__).startswith('1.'):
        print('ERROR: network_smoke.py is verified with TensorFlow 1.15.0; '
              'found {}. Use the prepared legacy environment.'.format(
                  tf.__version__), file=sys.stderr)
        return 2

    selected = set(FAMILIES if args.family == 'all' else (args.family,))
    checks = (
        ('core', _core), ('resnet', _resnet), ('unet', _unet),
        ('fcn', _fcn), ('deepmedic', _deepmedic),
        ('autoencoder', _autoencoder), ('gan', _gan),
        ('super-resolution', _super_resolution))
    try:
        for name, check in checks:
            if name in selected:
                check(tf, np)
    except (AssertionError, ImportError, TypeError, ValueError) as exc:
        print('FAIL: {}: {}'.format(type(exc).__name__, exc),
              file=sys.stderr)
        return 1
    print('Tiny graph smoke checks completed without training or data I/O.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
