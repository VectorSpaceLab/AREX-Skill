import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from iterate_prompts import iterate_prompts


def examples():
    return [
        {"premise": "The kids are outdoors.", "hypothesis": "Children are outside.", "label": 0, "keep": True},
        {"premise": "A person sleeps.", "hypothesis": "Someone is awake.", "label": 1, "keep": False},
    ]


def test_two_prompts_two_examples_produce_rows():
    templates = [
        {"id": "a", "name": "question", "template": "{{premise}} Is {{hypothesis}} true? ||| {{answer_choices[label]}}", "answer_choices": ["Yes", "No", "Maybe"]},
        {"id": "b", "name": "based", "template": "{{premise}} Based on this, {{hypothesis}}? ||| {{answer_choices[label]}}", "answer_choices": ["Yes", "No", "Maybe"]},
    ]
    report = iterate_prompts(examples(), templates)
    assert report["ok"] is True
    assert len(report["rows"]) == 4
    assert report["coverage"]["a"]["produced"] == 2
    assert report["variation_summary"]["template_count"] == 2


def test_skipped_condition_is_counted():
    templates = [{"id": "skip", "name": "conditional", "template": "{% if keep %}{{premise}}{% endif %} ||| label"}]
    report = iterate_prompts(examples(), templates, include_skipped=True)
    assert report["ok"] is True
    assert report["coverage"]["skip"]["produced"] == 1
    assert report["coverage"]["skip"]["skipped"] == 1
    assert len(report["rows"]) == 2


def test_render_errors_are_preserved():
    templates = [{"id": "bad", "name": "bad", "template": "{{missing}} ||| x"}]
    report = iterate_prompts(examples(), templates, include_skipped=True)
    assert report["ok"] is False
    assert report["coverage"]["bad"]["errors"] == 2
    assert "bad[0]" in report["errors"][0]


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")


def test_skipped_rows_are_excluded_by_default():
    templates = [{"id": "skip", "name": "conditional", "template": "{% if keep %}{{premise}}{% endif %} ||| label"}]
    report = iterate_prompts(examples(), templates)
    assert report["ok"] is True
    assert len(report["rows"]) == 1
