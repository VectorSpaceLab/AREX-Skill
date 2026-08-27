#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bundled LaneNet single-image inference wrapper.

This is adapted from the repository's tools/test_lanenet.py. It keeps the core
preprocessing, TensorFlow graph, checkpoint restore, and postprocess behavior,
but adds preflight validation plus noninteractive save options for agent/CI use.
Run it from the LaneNet repository root or pass --repo_root.
"""

import argparse
import json
import os
import os.path as ops
import sys
import time


def args_str2bool(arg_value):
    """Parse common boolean spellings for CLI flags."""
    if isinstance(arg_value, bool):
        return arg_value
    if arg_value is None:
        raise argparse.ArgumentTypeError('Boolean value expected.')
    value = str(arg_value).strip().lower()
    if value in ('yes', 'true', 't', 'y', '1', 'on'):
        return True
    if value in ('no', 'false', 'f', 'n', '0', 'off'):
        return False
    raise argparse.ArgumentTypeError('Unsupported boolean value: {}'.format(arg_value))


def init_args(argv=None):
    parser = argparse.ArgumentParser(
        description='Run LaneNet checkpoint inference on one image with safe preflight and optional saved outputs.'
    )
    parser.add_argument('--image_path', type=str, required=True, help='Input image path; relative paths resolve from repo root')
    parser.add_argument('--weights_path', type=str, required=True, help='Checkpoint base path or checkpoint directory')
    parser.add_argument('--with_lane_fit', type=args_str2bool, default=True, help='Whether to run TuSimple lane fitting')
    parser.add_argument('--repo_root', type=str, default='.', help='LaneNet repository root; default: current directory')
    parser.add_argument('--save_dir', type=str, default='', help='Optional directory for noninteractive output images and summary')
    parser.add_argument('--show', type=args_str2bool, default=False, help='Display matplotlib windows; default: 0')
    parser.add_argument('--loop_times', type=int, default=1, help='Forward passes for timing; use 1 for smoke checks')
    parser.add_argument('--use_moving_average', type=args_str2bool, default=True,
                        help='Restore moving-average variables; default matches original test script')
    parser.add_argument('--ipm_remap_file', type=str, default='./data/tusimple_ipm_remap.yml',
                        help='IPM remap YAML path; relative paths resolve from repo root')
    parser.add_argument('--min_area_threshold', type=int, default=100, help='Small connected-component removal threshold')
    parser.add_argument('--force_cpu', type=args_str2bool, default=False, help='Hide CUDA devices before TensorFlow import')
    return parser.parse_args(argv)


def _abspath_from_repo(repo_root, path_value):
    if not path_value:
        return path_value
    if ops.isabs(path_value):
        return ops.abspath(path_value)
    return ops.abspath(ops.join(repo_root, path_value))


def _prepare_repo(repo_root, force_cpu=False):
    repo_root = ops.abspath(repo_root)
    required = ['lanenet_model', 'local_utils', 'config']
    missing = [name for name in required if not ops.exists(ops.join(repo_root, name))]
    if missing:
        raise RuntimeError(
            'repo_root does not look like a LaneNet checkout; missing: {}'.format(', '.join(missing))
        )
    if force_cpu:
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.chdir(repo_root)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    return repo_root


def _strip_checkpoint_suffix(path_value):
    suffixes = ['.index', '.meta', '.data-00000-of-00001']
    for suffix in suffixes:
        if path_value.endswith(suffix):
            return path_value[:-len(suffix)]
    marker = '.data-'
    if marker in path_value:
        return path_value.split(marker)[0]
    return path_value


def _resolve_checkpoint(weights_path, repo_root, tf_module):
    candidate = _abspath_from_repo(repo_root, weights_path)
    if ops.isdir(candidate):
        latest = tf_module.train.latest_checkpoint(candidate)
        if latest:
            return latest
        raise FileNotFoundError('No TensorFlow checkpoint state found in directory: {}'.format(candidate))

    base = _strip_checkpoint_suffix(candidate)
    try:
        if tf_module.train.checkpoint_exists(base):
            return base
    except Exception:
        pass
    if ops.exists(base + '.index') or ops.exists(base + '.meta'):
        return base
    # Some checkpoints have nonstandard data shard names; accept them when present.
    parent = ops.dirname(base) or '.'
    stem = ops.basename(base)
    if ops.isdir(parent):
        for name in os.listdir(parent):
            if name.startswith(stem + '.data-'):
                return base
    raise FileNotFoundError(
        'Checkpoint not found. Pass the checkpoint base path, not just a missing directory or shard: {}'.format(
            weights_path
        )
    )


def minmax_scale(input_arr, np_module):
    min_val = np_module.min(input_arr)
    max_val = np_module.max(input_arr)
    denom = max_val - min_val
    if abs(float(denom)) < 1e-12:
        return np_module.zeros_like(input_arr, dtype=np_module.float32)
    return (input_arr - min_val) * 255.0 / denom


def _make_embedding_vis(instance_image, np_module):
    height, width = instance_image.shape[:2]
    channels = instance_image.shape[2] if len(instance_image.shape) == 3 else 1
    vis = np_module.zeros((height, width, 3), dtype=np_module.uint8)
    for idx in range(min(channels, 3)):
        vis[:, :, idx] = np_module.asarray(minmax_scale(instance_image[:, :, idx], np_module), dtype=np_module.uint8)
    return vis


def _write_image(cv2_module, path_value, image):
    os.makedirs(ops.dirname(path_value), exist_ok=True)
    ok = cv2_module.imwrite(path_value, image)
    if not ok:
        raise RuntimeError('Failed to write image: {}'.format(path_value))


def _jsonable_fit_params(fit_params):
    if fit_params is None:
        return None
    serializable = []
    for item in fit_params:
        if hasattr(item, 'tolist'):
            serializable.append(item.tolist())
        else:
            serializable.append(item)
    return serializable


def test_lanenet(args):
    repo_root = _prepare_repo(args.repo_root, force_cpu=args.force_cpu)
    image_path = _abspath_from_repo(repo_root, args.image_path)
    remap_path = _abspath_from_repo(repo_root, args.ipm_remap_file)

    if not ops.exists(image_path):
        raise FileNotFoundError('image_path does not exist: {}'.format(args.image_path))
    if not ops.exists(remap_path):
        raise FileNotFoundError('IPM remap file does not exist: {}'.format(args.ipm_remap_file))
    if args.loop_times < 1:
        raise ValueError('--loop_times must be >= 1')

    import cv2
    import numpy as np
    import tensorflow as tf

    from lanenet_model import lanenet
    from lanenet_model import lanenet_postprocess
    from local_utils.config_utils import parse_config_utils

    cfg = parse_config_utils.lanenet_cfg
    checkpoint_path = _resolve_checkpoint(args.weights_path, repo_root, tf)

    print('Start reading image and preprocessing')
    t_start = time.time()
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError('OpenCV could not read image_path: {}'.format(args.image_path))
    image_vis = image.copy()
    image = cv2.resize(image, (512, 256), interpolation=cv2.INTER_LINEAR)
    image = image / 127.5 - 1.0
    print('Image load complete, cost time: {:.5f}s'.format(time.time() - t_start))

    input_tensor = tf.placeholder(dtype=tf.float32, shape=[1, 256, 512, 3], name='input_tensor')
    net = lanenet.LaneNet(phase='test', cfg=cfg)
    binary_seg_ret, instance_seg_ret = net.inference(input_tensor=input_tensor, name='LaneNet')

    postprocessor = lanenet_postprocess.LaneNetPostProcessor(cfg=cfg, ipm_remap_file_path=remap_path)

    sess_config = tf.ConfigProto()
    sess_config.gpu_options.per_process_gpu_memory_fraction = cfg.GPU.GPU_MEMORY_FRACTION
    sess_config.gpu_options.allow_growth = cfg.GPU.TF_ALLOW_GROWTH
    sess_config.gpu_options.allocator_type = 'BFC'

    if args.use_moving_average:
        with tf.variable_scope(name_or_scope='moving_avg'):
            variable_averages = tf.train.ExponentialMovingAverage(cfg.SOLVER.MOVING_AVE_DECAY)
            variables_to_restore = variable_averages.variables_to_restore()
        saver = tf.train.Saver(variables_to_restore)
    else:
        saver = tf.train.Saver()

    sess = tf.Session(config=sess_config)
    saved_outputs = {}
    fit_params = None
    mask_image = None
    source_overlay = None
    try:
        with sess.as_default():
            print('Restoring checkpoint: {}'.format(checkpoint_path))
            saver.restore(sess=sess, save_path=checkpoint_path)

            t_start = time.time()
            binary_seg_image = None
            instance_seg_image = None
            for _ in range(args.loop_times):
                binary_seg_image, instance_seg_image = sess.run(
                    [binary_seg_ret, instance_seg_ret],
                    feed_dict={input_tensor: [image]}
                )
            avg_time = (time.time() - t_start) / float(args.loop_times)
            print('Single image inference cost time: {:.5f}s'.format(avg_time))

            postprocess_result = postprocessor.postprocess(
                binary_seg_result=binary_seg_image[0],
                instance_seg_result=instance_seg_image[0],
                min_area_threshold=args.min_area_threshold,
                source_image=image_vis.copy(),
                with_lane_fit=args.with_lane_fit,
                data_source='tusimple'
            )
            mask_image = postprocess_result['mask_image']
            fit_params = postprocess_result['fit_params']
            source_overlay = postprocess_result['source_image']

            if args.with_lane_fit and fit_params is not None:
                print('Model fitted {} lanes'.format(len(fit_params)))
                for idx, params in enumerate(fit_params):
                    print('Fitted 2-order lane {} curve param: {}'.format(idx + 1, params))
            elif mask_image is None:
                print('Postprocess did not produce a mask; inspect binary output and DBSCAN settings.')

            embedding_image = _make_embedding_vis(instance_seg_image[0], np)
            binary_vis = np.asarray(binary_seg_image[0] * 255, dtype=np.uint8)

            if args.save_dir:
                save_dir = _abspath_from_repo(repo_root, args.save_dir)
                os.makedirs(save_dir, exist_ok=True)
                outputs = {
                    'source_image': ('source_image.png', image_vis),
                    'binary_image': ('binary_image.png', binary_vis),
                    'instance_embedding': ('instance_embedding.png', embedding_image),
                }
                if mask_image is not None:
                    outputs['mask_image'] = ('mask_image.png', mask_image)
                if source_overlay is not None:
                    outputs['source_overlay'] = ('source_overlay.png', source_overlay)
                for key, (filename, data) in outputs.items():
                    output_path = ops.join(save_dir, filename)
                    _write_image(cv2, output_path, data)
                    saved_outputs[key] = output_path
                summary = {
                    'image_shape_original': list(image_vis.shape),
                    'network_input_shape': [1, 256, 512, 3],
                    'binary_output_shape': list(binary_seg_image.shape),
                    'instance_output_shape': list(instance_seg_image.shape),
                    'with_lane_fit': bool(args.with_lane_fit),
                    'use_moving_average': bool(args.use_moving_average),
                    'checkpoint_path': checkpoint_path,
                    'mask_produced': mask_image is not None,
                    'fit_count': 0 if fit_params is None else len(fit_params),
                    'fit_params': _jsonable_fit_params(fit_params),
                    'saved_outputs': saved_outputs,
                }
                summary_path = ops.join(save_dir, 'postprocess_summary.json')
                with open(summary_path, 'w', encoding='utf-8') as file_obj:
                    json.dump(summary, file_obj, indent=2, sort_keys=True)
                saved_outputs['summary'] = summary_path
                print('Saved outputs under: {}'.format(save_dir))

            if args.show:
                import matplotlib.pyplot as plt
                plt.figure('mask_image')
                if mask_image is not None:
                    plt.imshow(mask_image[:, :, (2, 1, 0)])
                plt.figure('src_image')
                plt.imshow(image_vis[:, :, (2, 1, 0)])
                plt.figure('instance_image')
                plt.imshow(embedding_image[:, :, (2, 1, 0)])
                plt.figure('binary_image')
                plt.imshow(binary_vis, cmap='gray')
                plt.show()
    finally:
        sess.close()

    return saved_outputs


def main(argv=None):
    args = init_args(argv)
    test_lanenet(args)


if __name__ == '__main__':
    main()
