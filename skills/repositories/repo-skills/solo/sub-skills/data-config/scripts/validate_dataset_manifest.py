#!/usr/bin/env python3
"""Read-only structural/path validator for legacy SOLO dataset manifests.

This intentionally uses only the standard library. It never downloads,
rewrites, links, decodes images, imports mmcv/torch, or runs conversions.
"""
from __future__ import print_function

import argparse
import json
import math
import os
import sys
import xml.etree.ElementTree as ET


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp'}
VOC_CLASSES = {
    'aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus', 'car', 'cat',
    'chair', 'cow', 'diningtable', 'dog', 'horse', 'motorbike', 'person',
    'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor'
}


class Report(object):
    def __init__(self, strict=False):
        self.strict = strict
        self.errors = []
        self.warnings = []
        self.checked_images = 0
        self.checked_annotations = 0

    def error(self, message):
        self.errors.append(message)

    def warning(self, message):
        self.warnings.append(message)

    def maybe(self, message):
        if self.strict:
            self.error(message)
        else:
            self.warning(message)

    def path(self, path, label):
        if not path:
            self.error('%s is empty' % label)
            return False
        if not os.path.exists(path):
            if os.path.islink(path):
                self.error('%s is a broken symlink: %s' % (label, path))
            else:
                self.error('%s does not exist: %s' % (label, path))
            return False
        if os.path.isdir(path):
            self.error('%s is a directory, expected a file: %s' % (label, path))
            return False
        return True


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def integer_like(value):
    return finite_number(value) and int(value) == value


def safe_join(root, relative, label, report):
    if not isinstance(relative, str) or not relative.strip():
        report.error('%s must be a non-empty string' % label)
        return None
    if os.path.isabs(relative):
        report.maybe('%s is absolute; portability is reduced: %s' % (label, relative))
        return os.path.normpath(relative)
    return os.path.normpath(os.path.join(root, relative))


def check_image_path(path, label, report):
    if report.path(path, label):
        report.checked_images += 1


def read_json(path, report):
    try:
        with open(path, 'r', encoding='utf-8') as stream:
            return json.load(stream)
    except (OSError, ValueError) as exc:
        report.error('cannot parse JSON %s: %s' % (path, exc))
        return None


def check_coco(args, report):
    if not report.path(args.ann, 'COCO annotation file'):
        return
    data = read_json(args.ann, report)
    if not isinstance(data, dict):
        report.error('COCO root must be an object')
        return
    images = data.get('images')
    annotations = data.get('annotations')
    categories = data.get('categories')
    for name, value in [('images', images), ('annotations', annotations), ('categories', categories)]:
        if not isinstance(value, list):
            report.error('COCO %s must be an array' % name)
    if not all(isinstance(value, list) for value in [images, annotations, categories]):
        return

    image_ids = set()
    image_by_id = {}
    for index, image in enumerate(images):
        prefix = 'COCO images[%d]' % index
        if not isinstance(image, dict):
            report.error('%s must be an object' % prefix)
            continue
        image_id = image.get('id')
        if image_id in image_ids:
            report.error('%s duplicates image id %r' % (prefix, image_id))
        image_ids.add(image_id)
        image_by_id[image_id] = image
        filename = image.get('file_name')
        width, height = image.get('width'), image.get('height')
        if not isinstance(filename, str) or not filename:
            report.error('%s.file_name must be a non-empty string' % prefix)
        if not (integer_like(width) and width > 0 and integer_like(height) and height > 0):
            report.error('%s width/height must be positive integers' % prefix)
        if isinstance(filename, str):
            path = safe_join(args.image_root, filename, prefix + '.file_name', report)
            if path:
                check_image_path(path, prefix + ' image', report)

    category_ids = set()
    for index, category in enumerate(categories):
        prefix = 'COCO categories[%d]' % index
        if not isinstance(category, dict):
            report.error('%s must be an object' % prefix)
            continue
        category_id = category.get('id')
        name = category.get('name')
        if category_id in category_ids:
            report.error('%s duplicates category id %r' % (prefix, category_id))
        category_ids.add(category_id)
        if not isinstance(name, str) or not name.strip():
            report.error('%s.name must be non-empty' % prefix)

    annotation_ids = set()
    for index, annotation in enumerate(annotations):
        prefix = 'COCO annotations[%d]' % index
        if not isinstance(annotation, dict):
            report.error('%s must be an object' % prefix)
            continue
        annotation_id = annotation.get('id')
        if annotation_id in annotation_ids:
            report.error('%s duplicates annotation id %r' % (prefix, annotation_id))
        annotation_ids.add(annotation_id)
        if annotation.get('image_id') not in image_ids:
            report.error('%s.image_id does not resolve: %r' % (prefix, annotation.get('image_id')))
        if annotation.get('category_id') not in category_ids:
            report.error('%s.category_id does not resolve: %r' % (prefix, annotation.get('category_id')))
        bbox = annotation.get('bbox')
        if not (isinstance(bbox, list) and len(bbox) == 4 and all(finite_number(x) for x in bbox)):
            report.error('%s.bbox must be four finite numbers' % prefix)
        elif bbox[2] <= 0 or bbox[3] <= 0:
            report.error('%s.bbox width/height must be positive' % prefix)
        image = image_by_id.get(annotation.get('image_id'))
        if image and isinstance(bbox, list) and len(bbox) == 4 and all(finite_number(x) for x in bbox):
            if bbox[0] < 0 or bbox[1] < 0 or bbox[0] + bbox[2] > image.get('width', 0) or bbox[1] + bbox[3] > image.get('height', 0):
                report.maybe('%s.bbox extends outside image bounds' % prefix)
        if 'area' in annotation and (not finite_number(annotation['area']) or annotation['area'] < 0):
            report.error('%s.area must be a non-negative finite number' % prefix)
        if args.require_masks and 'segmentation' not in annotation:
            report.error('%s lacks segmentation required by --require-masks' % prefix)
        report.checked_annotations += 1


def child_text(element, path, label, report):
    node = element.find(path)
    if node is None or node.text is None or not node.text.strip():
        report.error('%s is missing %s' % (label, path))
        return None
    return node.text.strip()


def check_voc_xml(xml_path, image_path, label, report, wider=False):
    if not report.path(xml_path, label + ' XML'):
        return
    try:
        root = ET.parse(xml_path).getroot()
    except (OSError, ET.ParseError) as exc:
        report.error('%s XML parse failed: %s' % (label, exc))
        return
    width_text = child_text(root, 'size/width', label, report)
    height_text = child_text(root, 'size/height', label, report)
    try:
        width, height = int(width_text), int(height_text)
        if width <= 0 or height <= 0:
            raise ValueError
    except (TypeError, ValueError):
        report.error('%s XML size must be positive integers' % label)
        width = height = None
    if image_path is not None:
        check_image_path(image_path, label + ' image', report)
    for index, obj in enumerate(root.findall('object')):
        object_label = '%s object[%d]' % (label, index)
        name = child_text(obj, 'name', object_label, report)
        if not wider and name not in VOC_CLASSES:
            report.error('%s has unknown VOC class %r' % (object_label, name))
        if wider and name != 'face':
            report.error('%s must use class face, got %r' % (object_label, name))
        difficult = child_text(obj, 'difficult', object_label, report)
        if difficult is not None and difficult not in ('0', '1'):
            report.error('%s.difficult must be 0 or 1' % object_label)
        coords = []
        for field in ('xmin', 'ymin', 'xmax', 'ymax'):
            text = child_text(obj, 'bndbox/' + field, object_label, report)
            try:
                coords.append(float(text))
            except (TypeError, ValueError):
                report.error('%s bbox %s is not numeric' % (object_label, field))
        if len(coords) == 4 and all(math.isfinite(x) for x in coords):
            if coords[2] <= coords[0] or coords[3] <= coords[1]:
                report.error('%s bbox is inverted or empty' % object_label)
            if width is not None and (coords[0] < 0 or coords[1] < 0 or coords[2] > width or coords[3] > height):
                report.maybe('%s bbox extends outside image bounds' % object_label)
        report.checked_annotations += 1


def read_ids(path, report):
    if not report.path(path, 'split list'):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as stream:
            ids = [line.strip() for line in stream if line.strip()]
    except OSError as exc:
        report.error('cannot read split list: %s' % exc)
        return []
    if not ids:
        report.error('split list is empty: %s' % path)
    return ids


def check_voc(args, report, wider=False):
    ids = read_ids(args.ann, report)
    root = args.dataset_root
    for image_id in ids:
        label = '%s %s' % ('WIDER' if wider else 'VOC', image_id)
        xml_path = os.path.join(root, 'Annotations', image_id + '.xml')
        if wider:
            # WIDER XML supplies the folder used by the reader for the image.
            folder = None
            if report.path(xml_path, label + ' XML'):
                try:
                    folder = ET.parse(xml_path).getroot().findtext('folder')
                except (OSError, ET.ParseError):
                    pass
            image_path = os.path.join(root, folder or '', image_id + '.jpg')
        else:
            image_path = os.path.join(root, 'JPEGImages', image_id + '.jpg')
        check_voc_xml(xml_path, image_path, label, report, wider=wider)


def check_custom(args, report):
    if not report.path(args.ann, 'custom annotation file'):
        return
    data = read_json(args.ann, report)
    if not isinstance(data, list):
        report.error('custom annotation root must be an array of image records')
        return
    for index, record in enumerate(data):
        label = 'custom record[%d]' % index
        if not isinstance(record, dict):
            report.error('%s must be an object' % label)
            continue
        filename = record.get('filename')
        width, height = record.get('width'), record.get('height')
        if not isinstance(filename, str) or not filename:
            report.error('%s.filename must be non-empty' % label)
        if not (integer_like(width) and width > 0 and integer_like(height) and height > 0):
            report.error('%s width/height must be positive integers' % label)
        if isinstance(filename, str):
            path = safe_join(args.image_root, filename, label + '.filename', report)
            if path:
                check_image_path(path, label + ' image', report)
        ann = record.get('ann')
        if ann is None:
            report.maybe('%s has no ann field (acceptable for inference, not training)' % label)
            continue
        if not isinstance(ann, dict):
            report.error('%s.ann must be an object' % label)
            continue
        check_array = [('bboxes', 4), ('bboxes_ignore', 4)]
        for field, width_expected in check_array:
            values = ann.get(field, [])
            if not isinstance(values, list):
                report.error('%s.%s must be a list' % (label, field))
                continue
            for row_index, row in enumerate(values):
                if not (isinstance(row, list) and len(row) == width_expected and all(finite_number(x) for x in row)):
                    report.error('%s.%s[%d] must contain four finite numbers' % (label, field, row_index))
                elif row[2] <= row[0] or row[3] <= row[1]:
                    report.error('%s.%s[%d] is empty or inverted' % (label, field, row_index))
                report.checked_annotations += 1
        for field in ('labels', 'labels_ignore'):
            if field in ann and not isinstance(ann[field], list):
                report.error('%s.%s must be a list' % (label, field))
        if isinstance(ann.get('bboxes'), list) and isinstance(ann.get('labels'), list) and len(ann['bboxes']) != len(ann['labels']):
            report.error('%s bboxes/labels lengths differ' % label)
        if isinstance(ann.get('bboxes_ignore'), list) and isinstance(ann.get('labels_ignore', []), list) and len(ann['bboxes_ignore']) != len(ann.get('labels_ignore', [])):
            report.error('%s ignored bboxes/labels lengths differ' % label)


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Read-only SOLO dataset manifest validator')
    parser.add_argument('--format', required=True, choices=('coco', 'voc', 'wider', 'custom'))
    parser.add_argument('--ann', required=True, help='JSON file or split list')
    parser.add_argument('--image-root', default='.', help='root for COCO/custom relative filenames')
    parser.add_argument('--dataset-root', default='.', help='VOC/WIDER split root')
    parser.add_argument('--require-masks', action='store_true', help='require segmentation in every COCO annotation')
    parser.add_argument('--strict', action='store_true', help='turn warnings into errors')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    report = Report(strict=args.strict)
    if args.format == 'coco':
        check_coco(args, report)
    elif args.format == 'voc':
        check_voc(args, report)
    elif args.format == 'wider':
        check_voc(args, report, wider=True)
    else:
        check_custom(args, report)

    print('format=%s images_checked=%d annotations_checked=%d' % (args.format, report.checked_images, report.checked_annotations))
    for warning in report.warnings:
        print('WARNING: %s' % warning)
    for error in report.errors:
        print('ERROR: %s' % error)
    if report.errors:
        print('RESULT: FAIL (%d error(s), %d warning(s))' % (len(report.errors), len(report.warnings)))
        return 1
    print('RESULT: PASS (%d warning(s))' % len(report.warnings))
    return 0


if __name__ == '__main__':
    sys.exit(main())
