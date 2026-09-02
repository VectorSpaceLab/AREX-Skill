import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from validate_metadata import validate_metadata


def test_accepts_valid_snli_metadata():
    report = validate_metadata(
        {
            "name": "based on previous passage",
            "metrics": ["Accuracy"],
            "answer_choices": ["Yes", "No", "Maybe"],
            "valid_outputs_stated": True,
            "language": "en",
            "reference": "paper Figure 1",
        },
        [{"input": "Premise. Yes, no, or maybe?", "target": "Yes"}],
    )
    assert report["ok"] is True
    assert not report["errors"]


def test_rejects_unknown_metric():
    report = validate_metadata({"name": "x", "metrics": ["Bogus"], "reference": "r"})
    assert report["ok"] is False
    assert "unknown metric" in report["errors"][0]


def test_rejects_inconsistent_valid_outputs():
    report = validate_metadata({"name": "x", "valid_outputs_stated": True, "answer_choices": [], "reference": "r"})
    assert report["ok"] is False
    assert "answer_choices" in report["errors"][0]


def test_warns_on_target_boilerplate():
    report = validate_metadata(
        {"name": "x", "metrics": ["Accuracy"], "reference": "r"},
        [{"input": "Question?", "target": "The answer is Yes"}],
    )
    assert report["ok"] is True
    assert "boilerplate" in report["warnings"][0]


def test_requires_name():
    report = validate_metadata({"metrics": ["Accuracy"], "reference": "r"})
    assert report["ok"] is False
    assert "name" in report["errors"][0]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")


def test_rejects_unrendered_template_markers_in_input():
    report = validate_metadata({"name": "x", "metrics": ["Accuracy"], "reference": "r"}, [{"input": "{{premise}}", "target": "Yes"}])
    assert report["ok"] is False
    assert "unrendered" in report["errors"][0]
