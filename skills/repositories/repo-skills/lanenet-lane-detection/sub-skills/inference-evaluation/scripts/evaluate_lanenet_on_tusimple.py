#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bundled LaneNet TuSimple batch-evaluation wrapper.

This is adapted from the repository's tools/evaluate_lanenet_on_tusimple.py. It
keeps the checkpoint-backed graph, 512x256 preprocessing, DBSCAN/lane-fit
postprocess, and TuSimple output layout, but adds path validation and smoke-test
controls. Run it from the LaneNet repository root or pass --repo_root.
"""

import argparse
import json
import os
import os.path as ops
import sys
import time


def args_str2bool(arg_value):
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
        description='Run LaneNet checkpoint inference over a TuSimple-style test_set/clips image tree.'
    )
    parser.add_argument('--image_dir', type=str, required=True, help='TuSimple test image root, normally test_set/clips')
    parser.add_argument('--weights_path', type=str, required=True, help='Checkpoint base path or checkpoint directory')
    parser.add_argument('--save_dir', type=str, required=True, help='Output root for source-overlay images')
    parser.add_argument('--repo_root', type=str, default='.', help='LaneNet repository root; default: current directory')
    parser.add_argument('--max_images', type=int, default=0, help='Optional image cap for smoke checks; 0 means all images')
    parser.add_argument('--allow_non_tusimple_layout', type=args_str2bool, default=False,
                        help='Allow image paths without a clips component and save relative to image_dir')
    parser.add_argument('--skip_existing', type=args_str2bool, default=True, help='Skip already written output images')
    parser.add_argument('--use_moving_average', type=args_str2bool, default=False,
                        help='Restore moving-average variables; default matches original evaluator raw-variable Saver')
    parser.add_argument('--with_lane_fit', type=args_str2bool, default=True,
                        help='Whether to run TuSimple lane fitting during postprocess')
    parser.add_argument('--ipm_remap_file', type=str, default='./data/tusimple_ipm_remap.yml',
                        help='IPM remap YAML path; relative paths resolve from repo root')
    parser.add_argument('--min_area_threshold', type=int, default=100, help='Small connected-component removal threshold')
    parser.add_argument('--summary_jsonl', type=str, default='auto',
                        help='Summary JSONL path; auto writes save_dir/evaluation_summary.jsonl; none disables')
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


def _path_parts(path_value):
    normalized = ops.normpath(path_value)
    drive, tail = ops.splitdrive(normalized)
    parts = []
    while tail and tail != ops.sep:
        tail, part = ops.split(tail)
        if part:
            parts.append(part)
        else:
            break
    if tail == ops.sep:
        parts.append(ops.sep)
    if drive:
        parts.append(drive)
    return list(reversed(parts))


def _relative_output_path(image_path, image_dir, allow_non_tusimple_layout):
    # The original evaluator uses image_path.split('clips')[1]. Keep that
    # TuSimple behavior, but validate it before the TensorFlow run.
    parts = _path_parts(image_path)
    if 'clips' in parts:
        clip_index = len(parts) - 1 - list(reversed(parts)).index('clips')
        trailing = parts[clip_index + 1:]
        if trailing:
            return ops.join(*trailing)
        return ops.basename(image_path)
    if not allow_non_tusimple_layout:
        raise ValueError(
            'image path does not contain a clips component; use a TuSimple test_set/clips tree '
            'or pass --allow_non_tusimple_layout 1 for synthetic smoke data: {}'.format(image_path)
        )
    return ops.relpath(image_path, image_dir)


def _discover_images(src_dir, allow_non_tusimple_layout):
    image_list = []
    for root, _, files in os.walk(src_dir):
        for name in sorted(files):
            if name.lower().endswith('.jpg'):
                image_list.append(ops.join(root, name))
    image_list.sort()
    if not image_list:
        raise RuntimeError('No .jpg images found under image_dir: {}'.format(src_dir))
    if not allow_non_tusimple_layout:
        bad_paths = [path for path in image_list if 'clips' not in _path_parts(path)]
        if bad_paths:
            preview = bad_paths[0]
            raise RuntimeError(
                'Strict TuSimple layout expected, but at least one image path lacks clips: {}. '
                'Point --image_dir at test_set/clips or pass --allow_non_tusimple_layout 1 for smoke data.'.format(
                    preview
                )
            )
    return image_list


def _summary_path(save_dir, summary_jsonl):
    value = str(summary_jsonl).strip()
    if value.lower() in ('', '0', 'false', 'none', 'no', 'off'):
        return None
    if value.lower() == 'auto':
        return ops.join(save_dir, 'evaluation_summary.jsonl')
    if ops.isabs(value):
        return value
    return ops.abspath(value)


def eval_lanenet(args):
    repo_root = _prepare_repo(args.repo_root, force_cpu=args.force_cpu)
    src_dir = _abspath_from_repo(repo_root, args.image_dir)
    save_dir = _abspath_from_repo(repo_root, args.save_dir)
    remap_path = _abspath_from_repo(repo_root, args.ipm_remap_file)

    if not ops.exists(src_dir):
        raise FileNotFoundError('image_dir does not exist: {}'.format(args.image_dir))
    if not ops.isdir(src_dir):
        raise NotADirectoryError('image_dir is not a directory: {}'.format(args.image_dir))
    if not ops.exists(remap_path):
        raise FileNotFoundError('IPM remap file does not exist: {}'.format(args.ipm_remap_file))
    if args.max_images < 0:
        raise ValueError('--max_images must be >= 0')
    os.makedirs(save_dir, exist_ok=True)

    image_list = _discover_images(src_dir, args.allow_non_tusimple_layout)
    if args.max_images:
        image_list = image_list[:args.max_images]
    print('Found {} image(s) for LaneNet evaluation'.format(len(image_list)))

    import cv2
    import numpy as np
    import tensorflow as tf
    import tqdm

    from lanenet_model import lanenet
    from lanenet_model import lanenet_postprocess
    from local_utils.config_utils import parse_config_utils

    cfg = parse_config_utils.lanenet_cfg
    checkpoint_path = _resolve_checkpoint(args.weights_path, repo_root, tf)

    input_tensor = tf.placeholder(dtype=tf.float32, shape=[1, 256, 512, 3], name='input_tensor')
    net = lanenet.LaneNet(phase='test', cfg=cfg)
    binary_seg_ret, instance_seg_ret = net.inference(input_tensor=input_tensor, name='LaneNet')
    postprocessor = lanenet_postprocess.LaneNetPostProcessor(cfg=cfg, ipm_remap_file_path=remap_path)

    if args.use_moving_average:
        with tf.variable_scope(name_or_scope='moving_avg'):
            variable_averages = tf.train.ExponentialMovingAverage(cfg.SOLVER.MOVING_AVE_DECAY)
            variables_to_restore = variable_averages.variables_to_restore()
        saver = tf.train.Saver(variables_to_restore)
    else:
        saver = tf.train.Saver()

    sess_config = tf.ConfigProto()
    sess_config.gpu_options.per_process_gpu_memory_fraction = cfg.GPU.GPU_MEMORY_FRACTION
    sess_config.gpu_options.allow_growth = cfg.GPU.TF_ALLOW_GROWTH
    sess_config.gpu_options.allocator_type = 'BFC'

    summary_file_path = _summary_path(save_dir, args.summary_jsonl)
    if summary_file_path:
        os.makedirs(ops.dirname(summary_file_path), exist_ok=True)
        summary_file = open(summary_file_path, 'w', encoding='utf-8')
    else:
        summary_file = None

    avg_time_cost = []
    written = 0
    skipped = 0
    failed = 0
    sess = tf.Session(config=sess_config)
    try:
        with sess.as_default():
            print('Restoring checkpoint: {}'.format(checkpoint_path))
            saver.restore(sess=sess, save_path=checkpoint_path)

            for index, image_path in tqdm.tqdm(enumerate(image_list), total=len(image_list)):
                record = {
                    'image_path': image_path,
                    'output_path': None,
                    'status': 'pending',
                    'mask_produced': False,
                    'inference_time_sec': None,
                }
                try:
                    relative_output = _relative_output_path(image_path, src_dir, args.allow_non_tusimple_layout)
                    output_image_path = ops.join(save_dir, relative_output)
                    record['output_path'] = output_image_path
                    if args.skip_existing and ops.exists(output_image_path):
                        skipped += 1
                        record['status'] = 'skipped_existing'
                        if summary_file:
                            summary_file.write(json.dumps(record, sort_keys=True) + '\n')
                        continue

                    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
                    if image is None:
                        raise RuntimeError('OpenCV could not read image')
                    image_vis = image.copy()
                    image = cv2.resize(image, (512, 256), interpolation=cv2.INTER_LINEAR)
                    image = image / 127.5 - 1.0

                    t_start = time.time()
                    binary_seg_image, instance_seg_image = sess.run(
                        [binary_seg_ret, instance_seg_ret],
                        feed_dict={input_tensor: [image]}
                    )
                    elapsed = time.time() - t_start
                    avg_time_cost.append(elapsed)
                    record['inference_time_sec'] = elapsed

                    postprocess_result = postprocessor.postprocess(
                        binary_seg_result=binary_seg_image[0],
                        instance_seg_result=instance_seg_image[0],
                        min_area_threshold=args.min_area_threshold,
                        source_image=image_vis,
                        with_lane_fit=args.with_lane_fit,
                        data_source='tusimple'
                    )
                    source_image = postprocess_result['source_image']
                    record['mask_produced'] = postprocess_result['mask_image'] is not None

                    if index % 100 == 0 and avg_time_cost:
                        print('Mean inference time every single image: {:.5f}s'.format(np.mean(avg_time_cost)))
                        avg_time_cost = []

                    if source_image is None:
                        failed += 1
                        record['status'] = 'postprocess_no_source_image'
                    else:
                        os.makedirs(ops.dirname(output_image_path), exist_ok=True)
                        ok = cv2.imwrite(output_image_path, source_image)
                        if not ok:
                            raise RuntimeError('Failed to write output image')
                        written += 1
                        record['status'] = 'written'
                except Exception as err:  # keep batch records actionable without hiding failures
                    failed += 1
                    record['status'] = 'failed'
                    record['error'] = str(err)
                    print('Failed on {}: {}'.format(image_path, err), file=sys.stderr)
                finally:
                    if summary_file:
                        summary_file.write(json.dumps(record, sort_keys=True) + '\n')
                        summary_file.flush()
    finally:
        sess.close()
        if summary_file:
            summary_file.close()

    print('Evaluation complete: written={}, skipped={}, failed={}, save_dir={}'.format(
        written, skipped, failed, save_dir
    ))
    if summary_file_path:
        print('Summary JSONL: {}'.format(summary_file_path))
    if failed:
        raise RuntimeError('Evaluation completed with {} failed image(s); inspect summary JSONL.'.format(failed))


def main(argv=None):
    args = init_args(argv)
    eval_lanenet(args)


if __name__ == '__main__':
    main()
