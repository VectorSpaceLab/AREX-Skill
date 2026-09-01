import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from materialize_p3 import materialize_p3


def examples():
    return [
        {"premise": "The kids are outdoors.", "hypothesis": "Children are outside.", "label": 0},
        {"premise": "A person sleeps.", "hypothesis": "Someone is awake.", "label": 1},
    ]


def valid_template(template_id, name):
    return {
        "id": template_id,
        "name": name,
        "template": "{{premise}} Is it true that {{hypothesis}}? Yes, no, or maybe? ||| {{answer_choices[label]}}",
        "answer_choices": ["Yes", "No", "Maybe"],
        "metrics": ["Accuracy"],
        "valid_outputs_stated": True,
        "original_task": True,
        "language": "en",
        "reference": "paper Figure 1",
    }


def test_materializes_two_by_two_collection():
    report = materialize_p3("synthetic_snli", None, examples(), [valid_template("a", "nli"), valid_template("b", "nli")])
    assert report["ok"] is True
    assert len(report["records"]) == 4
    assert report["summary"]["produced_records"] == 4
    assert report["summary"]["metrics"] == ["Accuracy"]
    assert {record["template_id"] for record in report["records"]} == {"a", "b"}


def test_metadata_errors_are_reported():
    bad = valid_template("bad", "bad")
    bad["metrics"] = ["Bogus"]
    report = materialize_p3("synthetic_snli", None, examples(), [bad])
    assert report["ok"] is False
    assert "unknown metric" in report["errors"][0]


def test_skipped_rows_are_counted_not_emitted():
    template = valid_template("skip", "skip")
    template["template"] = "{% if label == 0 %}{{premise}}{% endif %} ||| {{answer_choices[label]}}"
    report = materialize_p3("synthetic_snli", None, examples(), [template])
    assert report["ok"] is True
    assert report["summary"]["produced_records"] == 1
    assert report["summary"]["skipped_records"] == 1


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")


def test_duplicate_template_names_keep_stable_ids():
    report = materialize_p3("synthetic_snli", None, examples(), [valid_template("a", "same"), valid_template("b", "same")])
    assert report["ok"] is True
    assert {record["template_id"] for record in report["records"]} == {"a", "b"}
