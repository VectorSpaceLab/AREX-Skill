import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from render_prompt import render_prompt


def test_snli_answer_choice_rendering():
    result = render_prompt(
        {"premise": "The kids are outdoors.", "hypothesis": "Children are outside.", "label": 0},
        '{{premise}} Based on the previous passage, is it true that "{{hypothesis}}"? Yes, no, or maybe? ||| {{ answer_choices[label] }}',
        ["Yes", "No", "Maybe"],
    )
    assert result["ok"] is True
    assert "The kids are outdoors" in result["input"]
    assert result["target"] == "Yes"
    assert result["skipped"] is False


def test_rejects_missing_separator():
    result = render_prompt({"text": "x"}, "{{text}}")
    assert result["ok"] is False
    assert "separator" in result["errors"][0]


def test_missing_field_is_diagnostic():
    result = render_prompt({"text": "x"}, "{{missing}} ||| target")
    assert result["ok"] is False
    assert "rendering failed" in result["errors"][0]


def test_empty_conditional_is_skipped():
    result = render_prompt({"keep": False}, "{% if keep %}shown{% endif %} ||| label")
    assert result["ok"] is True
    assert result["skipped"] is True


def test_deterministic_choice_helper():
    result = render_prompt({}, "Pick one ||| {{ choice(options) }}", {"options": ["bad"]})
    assert result["ok"] is False
    result = render_prompt({"options": ["a", "b", "c"]}, "Pick one ||| {{ choice(options) }}", None, choice_index=4)
    assert result["target"] == "b"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")


def test_rejects_multiple_separators():
    result = render_prompt({"text": "x"}, "{{text}} ||| a ||| b")
    assert result["ok"] is False
    assert "separator" in result["errors"][0]
