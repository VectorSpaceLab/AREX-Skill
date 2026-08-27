#!/usr/bin/env python3
"""Exercise the YOLOv5 Flask REST API route with a Flask test client and a dummy model."""

from __future__ import annotations

import argparse
import io
import os

from PIL import Image

from utils.flask_rest_api.restapi import DETECTION_URL, MAX_IMAGE_SIZE, app, models

MODEL_NAME = "yolov5s"
DETECTION_PATH = DETECTION_URL.replace("<model>", MODEL_NAME)


class DummyResults:
    class _Pandas:
        xyxy = [type("DummyDf", (), {"to_json": lambda self, orient: "[]"})()]

    def pandas(self):
        return self._Pandas()


class DummyModel:
    def __call__(self, im, size=640):
        return DummyResults()


def make_image_bytes(fmt: str = "PNG") -> io.BytesIO:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), color="white").save(buf, format=fmt)
    buf.seek(0)
    return buf


def post_image(client, file_obj, filename, headers=None):
    return client.post(
        DETECTION_PATH,
        data={"image": (file_obj, filename)},
        content_type="multipart/form-data",
        headers=headers,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a safe Flask REST API smoke test with a dummy model")
    parser.add_argument("--check-size-limit", action="store_true", help="also test the upload size limit")
    parser.add_argument("--api-key", default=None, help="optional API key value to verify auth handling")
    args = parser.parse_args()

    if args.api_key is not None:
        os.environ["API_KEY"] = args.api_key
    else:
        os.environ.pop("API_KEY", None)

    models.clear()
    models[MODEL_NAME] = DummyModel()
    app.config.update(TESTING=True)
    client = app.test_client()

    failures = []

    headers = {"X-API-Key": args.api_key} if args.api_key is not None else None

    ok = post_image(client, make_image_bytes(), "image.png", headers=headers)
    if ok.status_code != 200 or ok.data != b"[]":
        failures.append(f"expected 200 with [] for valid image, got {ok.status_code} and {ok.data!r}")

    bad_type = post_image(client, io.BytesIO(b"hello"), "payload.txt", headers=headers)
    if bad_type.status_code != 400:
        failures.append(f"expected 400 for invalid extension, got {bad_type.status_code}")

    bad_image = post_image(client, io.BytesIO(b"not really an image"), "fake.jpg", headers=headers)
    if bad_image.status_code != 400:
        failures.append(f"expected 400 for invalid image payload, got {bad_image.status_code}")

    if args.check_size_limit:
        oversized = post_image(client, io.BytesIO(b"a" * (MAX_IMAGE_SIZE + 1)), "large.jpg", headers=headers)
        if oversized.status_code != 413:
            failures.append(f"expected 413 for oversized upload, got {oversized.status_code}")

    if args.api_key is not None:
        denied = post_image(client, make_image_bytes(), "image.png", headers={"X-API-Key": "wrong"})
        if denied.status_code != 401:
            failures.append(f"expected 401 with mismatched API key, got {denied.status_code}")

    print(f"checked route: {DETECTION_PATH}")
    print(f"model registry: {sorted(models)}")
    if failures:
        print("failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
