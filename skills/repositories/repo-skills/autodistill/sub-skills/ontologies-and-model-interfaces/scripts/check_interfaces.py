#!/usr/bin/env python3
"""Run safe Autodistill ontology and interface conformance checks.

This script uses deterministic dummy classes only. It does not install plugin
packages, download model weights, use a GPU, label a real dataset, or train a
model.
"""
from __future__ import annotations

import argparse
import inspect

import numpy as np
import supervision as sv

from autodistill.detection import CaptionOntology, DetectionBaseModel, DetectionTargetModel
from autodistill.classification import ClassificationBaseModel
from autodistill.core.composed_detection_model import ComposedDetectionModel


class DummyDetector(DetectionBaseModel):
    def __init__(self, ontology: CaptionOntology) -> None:
        self.ontology = ontology

    def predict(self, input):  # type: ignore[override]
        return sv.Detections(
            xyxy=np.array([[1, 2, 10, 12]], dtype=float),
            confidence=np.array([0.8], dtype=float),
            class_id=np.array([0], dtype=int),
        )


class DummyDetectionTarget(DetectionTargetModel):
    def __init__(self) -> None:
        self.trained = False

    def predict(self, input: str, confidence: float = 0.5) -> sv.Detections:
        return sv.Detections(
            xyxy=np.array([[0, 0, 5, 5]], dtype=float),
            confidence=np.array([confidence], dtype=float),
            class_id=np.array([0], dtype=int),
        )

    def train(self):
        self.trained = True


class DummyClassifier(ClassificationBaseModel):
    def __init__(self, ontology: CaptionOntology) -> None:
        self.ontology = ontology

    def predict(self, input: str) -> sv.Classifications:
        return sv.Classifications(
            class_id=np.array([0], dtype=int),
            confidence=np.array([0.9], dtype=float),
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-composed", action="store_true", help="Skip constructing ComposedDetectionModel.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ontology = CaptionOntology({"square": "square"})
    assert ontology.prompts() == ["square"]
    assert ontology.classes() == ["square"]
    assert ontology.promptToClass("square") == "square"
    assert ontology.classToPrompt("square") == "square"
    try:
        CaptionOntology({})
    except ValueError:
        pass
    else:
        raise AssertionError("CaptionOntology({}) should raise ValueError")

    detector = DummyDetector(ontology)
    det = detector.predict("unused")
    assert isinstance(det, sv.Detections)
    assert det.class_id[0] == 0
    assert det.confidence[0] > 0

    target = DummyDetectionTarget()
    target.train()
    assert target.trained
    assert isinstance(target.predict("unused"), sv.Detections)

    classifier = DummyClassifier(ontology)
    cls = classifier.predict("unused")
    assert isinstance(cls, sv.Classifications)

    if not args.skip_composed:
        composed = ComposedDetectionModel(detector, classifier)
        assert composed.ontology.classes() == ["square"]

    sig = inspect.signature(DetectionBaseModel.label)
    for expected in ["input_folder", "extension", "output_folder", "sahi", "record_confidence", "nms_settings"]:
        assert expected in sig.parameters

    print("Autodistill ontology/interface conformance checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
