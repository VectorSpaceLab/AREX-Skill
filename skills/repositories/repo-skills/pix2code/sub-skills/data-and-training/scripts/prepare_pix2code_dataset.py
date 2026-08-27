#!/usr/bin/env python3
"""Validate, split, and convert pix2code paired datasets.

Examples:
    python prepare_pix2code_dataset.py validate --input datasets/web/all_data
    python prepare_pix2code_dataset.py split --input datasets/web/all_data --distribution 6
    python prepare_pix2code_dataset.py convert --input datasets/web/training_set --output datasets/web/training_features
"""

from __future__ import print_function

import argparse
import hashlib
import os
import shutil
import sys

import numpy as np

IMAGE_SIZE = 256
TRAINING_SET_NAME = "training_set"
EVALUATION_SET_NAME = "eval_set"


def list_pairs(input_path):
    pairs = []
    for name in sorted(os.listdir(input_path)):
        if not name.endswith('.gui'):
            continue
        base = name[:-4]
        gui = os.path.join(input_path, name)
        png = os.path.join(input_path, base + '.png')
        npz = os.path.join(input_path, base + '.npz')
        if os.path.isfile(png):
            pairs.append((base, gui, png, 'png'))
        elif os.path.isfile(npz):
            pairs.append((base, gui, npz, 'npz'))
    return pairs


def load_cv2():
    try:
        import cv2
        return cv2
    except Exception as exc:
        raise RuntimeError('OpenCV is required for convert but could not be imported: {}'.format(exc))


def preprocess_image(img_path):
    cv2 = load_cv2()
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError('Unable to read image {}'.format(img_path))
    img = cv2.resize(img, (IMAGE_SIZE, IMAGE_SIZE))
    img = img.astype('float32')
    img /= 255.0
    return img


def validate(input_path):
    pairs = list_pairs(input_path)
    if not pairs:
        raise ValueError('No paired .gui plus .png/.npz files found in {}'.format(input_path))
    missing = []
    for name in sorted(os.listdir(input_path)):
        if name.endswith('.gui'):
            base = name[:-4]
            if not (os.path.isfile(os.path.join(input_path, base + '.png')) or os.path.isfile(os.path.join(input_path, base + '.npz'))):
                missing.append(base)
    if missing:
        raise ValueError('Unpaired basenames: {}'.format(', '.join(missing)))
    print('PASS validate {} paired samples'.format(len(pairs)))
    return pairs


def split(input_path, distribution):
    pairs = validate(input_path)
    if distribution < 1:
        raise ValueError('distribution must be >= 1')
    total = len(pairs)
    if total % (distribution + 1) != 0:
        raise ValueError('sample count {} does not divide cleanly by distribution {}'.format(total, distribution))
    eval_count = total // (distribution + 1)
    train_count = total - eval_count
    print('Splitting datasets, training samples: {}, evaluation samples: {}'.format(train_count, eval_count))
    pairs = list(pairs)
    import random
    random.Random(1234).shuffle(pairs)
    eval_set = []
    train_set = []
    seen_hashes = []
    for base, gui, image, image_kind in pairs:
        with open(gui, 'r') as f:
            content = ''.join(f.readlines())
        content_hash = hashlib.sha256(content.replace(' ', '').replace('\n', '').encode('utf-8')).hexdigest()
        if len(eval_set) == eval_count:
            train_set.append((base, gui, image, image_kind))
            continue
        if content_hash in seen_hashes:
            train_set.append((base, gui, image, image_kind))
        else:
            eval_set.append((base, gui, image, image_kind))
            seen_hashes.append(content_hash)
    if len(eval_set) != eval_count:
        raise AssertionError('evaluation split count mismatch: {} != {}'.format(len(eval_set), eval_count))
    if len(train_set) != train_count:
        raise AssertionError('training split count mismatch: {} != {}'.format(len(train_set), train_count))
    base_dir = os.path.dirname(input_path)
    eval_dir = os.path.join(base_dir, EVALUATION_SET_NAME)
    train_dir = os.path.join(base_dir, TRAINING_SET_NAME)
    for path in (eval_dir, train_dir):
        if not os.path.exists(path):
            os.makedirs(path)
    for base, gui, image, image_kind in eval_set:
        shutil.copyfile(gui, os.path.join(eval_dir, base + '.gui'))
        shutil.copyfile(image, os.path.join(eval_dir, base + ('.png' if image_kind == 'png' else '.npz')))
    for base, gui, image, image_kind in train_set:
        shutil.copyfile(gui, os.path.join(train_dir, base + '.gui'))
        shutil.copyfile(image, os.path.join(train_dir, base + ('.png' if image_kind == 'png' else '.npz')))
    print('Training dataset: {}'.format(train_dir))
    print('Evaluation dataset: {}'.format(eval_dir))


def convert(input_path, output_path):
    pairs = validate(input_path)
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    print('Converting images to numpy arrays...')
    for base, gui, image, image_kind in pairs:
        if image_kind == 'npz':
            features = np.load(image)['features']
        else:
            features = preprocess_image(image)
        np.savez_compressed(os.path.join(output_path, base), features=features)
        retrieved = np.load(os.path.join(output_path, base + '.npz'))['features']
        if not np.array_equal(features, retrieved):
            raise AssertionError('Stored features do not match for {}'.format(base))
        shutil.copyfile(gui, os.path.join(output_path, base + '.gui'))
    print('Numpy arrays saved in {}'.format(output_path))


def build_parser():
    parser = argparse.ArgumentParser(description='Validate, split, and convert pix2code paired datasets.')
    sub = parser.add_subparsers(dest='command')

    p = sub.add_parser('validate')
    p.add_argument('--input', required=True)

    p = sub.add_parser('split')
    p.add_argument('--input', required=True)
    p.add_argument('--distribution', type=int, default=6)

    p = sub.add_parser('convert')
    p.add_argument('--input', required=True)
    p.add_argument('--output', required=True)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command is None:
        raise ValueError('a subcommand is required: validate, split, or convert')
    if args.command == 'validate':
        validate(args.input)
    elif args.command == 'split':
        split(args.input, args.distribution)
    elif args.command == 'convert':
        convert(args.input, args.output)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print('ERROR: {}: {}'.format(exc.__class__.__name__, exc), file=sys.stderr)
        raise SystemExit(2)
