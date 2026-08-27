#!/usr/bin/env python3
"""Validate a tiny, local COCO bbox evaluation fixture.

This is intentionally dependency-free: it does not import TensorRT, CUDA,
TensorFlow, OpenCV, pycocotools, or progressbar2; it never downloads data and
never runs inference. It is a layout/serialization gate, not an mAP evaluator.
"""

import argparse
import json
import math
import sys
from pathlib import Path


# This helper is a synthetic-fixture checker, not a 5K evaluation preflight.
MAX_FIXTURE_IMAGES = 32
MAX_FIXTURE_RESULTS = 1024


def fail(errors, message):
    errors.append(message)


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def read_json(path, errors, label):
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        fail(errors, "%s does not exist: %s" % (label, path))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(errors, "%s is not valid UTF-8 JSON (%s): %s" % (label, exc, path))
    return None


def image_ids_from_directory(images_dir, errors):
    if not images_dir.is_dir():
        fail(errors, "images directory does not exist or is not a directory: %s" % images_dir)
        return set()

    jpgs = [item for item in images_dir.iterdir() if item.is_file() and item.name.endswith(".jpg")]
    if not jpgs:
        fail(errors, "images directory contains no lowercase .jpg files: %s" % images_dir)
    if len(jpgs) > MAX_FIXTURE_IMAGES:
        fail(
            errors,
            "refusing %d images: this helper accepts at most %d tiny-fixture images; "
            "do not use it for the 5K COCO evaluation" % (len(jpgs), MAX_FIXTURE_IMAGES),
        )

    ids = set()
    for image in sorted(jpgs):
        stem = image.name.rsplit(".", 1)[0]
        token = stem.rsplit("_", 1)[-1]
        try:
            image_id = int(token)
        except ValueError:
            fail(errors, "JPEG filename has no final numeric image ID: %s" % image.name)
            continue
        if image_id in ids:
            fail(errors, "duplicate image ID %d in JPEG filenames" % image_id)
        ids.add(image_id)
    return ids


def validate_annotations(document, errors):
    if not isinstance(document, dict):
        fail(errors, "annotations must be a JSON object")
        return set(), set()

    images = document.get("images")
    annotations = document.get("annotations")
    categories = document.get("categories")
    for key, value in (("images", images), ("annotations", annotations), ("categories", categories)):
        if not isinstance(value, list):
            fail(errors, "annotations.%s must be an array" % key)

    if not all(isinstance(value, list) for value in (images, annotations, categories)):
        return set(), set()

    image_ids = set()
    for index, image in enumerate(images):
        if not isinstance(image, dict) or not is_int(image.get("id")):
            fail(errors, "images[%d].id must be an integer" % index)
            continue
        image_id = image["id"]
        if image_id in image_ids:
            fail(errors, "duplicate annotation image id: %d" % image_id)
        image_ids.add(image_id)

    category_ids = set()
    for index, category in enumerate(categories):
        if not isinstance(category, dict) or not is_int(category.get("id")):
            fail(errors, "categories[%d].id must be an integer" % index)
            continue
        category_id = category["id"]
        if category_id in category_ids:
            fail(errors, "duplicate annotation category id: %d" % category_id)
        category_ids.add(category_id)

    annotation_ids = set()
    for index, annotation in enumerate(annotations):
        if not isinstance(annotation, dict):
            fail(errors, "annotations[%d] must be an object" % index)
            continue
        annotation_id = annotation.get("id")
        if annotation_id is not None:
            if not is_int(annotation_id):
                fail(errors, "annotations[%d].id must be an integer when present" % index)
            elif annotation_id in annotation_ids:
                fail(errors, "duplicate ground-truth annotation id: %d" % annotation_id)
            else:
                annotation_ids.add(annotation_id)
        image_id = annotation.get("image_id")
        if not is_int(image_id):
            fail(errors, "annotations[%d].image_id must be an integer" % index)
        elif image_id not in image_ids:
            fail(errors, "annotations[%d] references unknown image_id %d" % (index, image_id))
        category_id = annotation.get("category_id")
        if not is_int(category_id):
            fail(errors, "annotations[%d].category_id must be an integer" % index)
        elif category_id not in category_ids:
            fail(errors, "annotations[%d] references unknown category_id %d" % (index, category_id))
        validate_bbox(annotation.get("bbox"), errors, "annotations[%d].bbox" % index)
        if "area" in annotation and not finite_number(annotation["area"]):
            fail(errors, "annotations[%d].area must be finite when present" % index)
        if "iscrowd" in annotation and annotation["iscrowd"] not in (0, 1):
            fail(errors, "annotations[%d].iscrowd must be 0 or 1 when present" % index)

    if len(images) > MAX_FIXTURE_IMAGES:
        fail(
            errors,
            "refusing %d annotation images: this helper accepts at most %d tiny-fixture images; "
            "do not use it for the 5K COCO evaluation" % (len(images), MAX_FIXTURE_IMAGES),
        )
    if not image_ids:
        fail(errors, "annotations.images must contain at least one image")
    if not category_ids:
        fail(errors, "annotations.categories must contain at least one category")
    return image_ids, category_ids


def validate_bbox(bbox, errors, label):
    if not isinstance(bbox, list) or len(bbox) != 4:
        fail(errors, "%s must be [x, y, width, height]" % label)
        return
    if not all(finite_number(value) for value in bbox):
        fail(errors, "%s values must be finite numbers" % label)
        return
    if float(bbox[2]) <= 0 or float(bbox[3]) <= 0:
        fail(errors, "%s width and height must be positive" % label)


def validate_results(document, image_ids, category_ids, errors):
    if not isinstance(document, list):
        fail(errors, "results must be a JSON array")
        return
    if len(document) > MAX_FIXTURE_RESULTS:
        fail(
            errors,
            "refusing %d results: this helper accepts at most %d tiny-fixture results; "
            "do not use it for a full evaluation" % (len(document), MAX_FIXTURE_RESULTS),
        )
    for index, result in enumerate(document):
        if not isinstance(result, dict):
            fail(errors, "results[%d] must be an object" % index)
            continue
        image_id = result.get("image_id")
        if not is_int(image_id):
            fail(errors, "results[%d].image_id must be an integer" % index)
        elif image_id not in image_ids:
            fail(errors, "results[%d] references unknown image_id %d" % (index, image_id))
        category_id = result.get("category_id")
        if not is_int(category_id):
            fail(errors, "results[%d].category_id must be an integer" % index)
        elif category_id not in category_ids:
            fail(errors, "results[%d] references unknown category_id %d" % (index, category_id))
        validate_bbox(result.get("bbox"), errors, "results[%d].bbox" % index)
        score = result.get("score")
        if not finite_number(score) or not 0 <= float(score) <= 1:
            fail(errors, "results[%d].score must be a finite number in [0, 1]" % index)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate a tiny local COCO bbox fixture; never runs inference or mAP."
    )
    parser.add_argument("--images-dir", required=True, type=Path)
    parser.add_argument("--annotations", required=True, type=Path)
    parser.add_argument("--results", required=True, type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    errors = []
    jpg_ids = image_ids_from_directory(args.images_dir, errors)
    annotations = read_json(args.annotations, errors, "annotations")
    result_document = read_json(args.results, errors, "results")
    annotation_image_ids, category_ids = validate_annotations(annotations, errors) if annotations is not None else (set(), set())

    if jpg_ids and annotation_image_ids and jpg_ids != annotation_image_ids:
        missing = sorted(annotation_image_ids - jpg_ids)
        extra = sorted(jpg_ids - annotation_image_ids)
        fail(errors, "JPEG IDs must exactly match annotation image IDs (missing=%s extra=%s)" % (missing, extra))
    if result_document is not None:
        validate_results(result_document, annotation_image_ids, category_ids, errors)

    if errors:
        print("FAIL: COCO evaluation layout is not a valid tiny fixture", file=sys.stderr)
        for error in errors:
            print("- %s" % error, file=sys.stderr)
        return 1

    print(
        "PASS: tiny fixture layout is valid (%d JPEGs, %d categories, %d results)"
        % (len(jpg_ids), len(category_ids), len(result_document))
    )
    print("No inference or COCO mAP evaluation was run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
