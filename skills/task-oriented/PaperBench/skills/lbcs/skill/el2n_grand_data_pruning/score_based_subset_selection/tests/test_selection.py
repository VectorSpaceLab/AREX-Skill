import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from select_subset import select_high_score, select_offset_window


def test_high_score_fraction_selection():
    records = [
        {"id": "easy", "score": 0.1},
        {"id": "hard", "score": 0.9},
        {"id": "mid", "score": 0.5},
        {"id": "harder", "score": 0.8},
    ]
    result = select_high_score(records, retain_fraction=0.5)
    assert result["selected_ids"] == ["hard", "harder"]
    assert set(result["pruned_ids"]) == {"easy", "mid"}


def test_tie_break_by_id():
    records = [{"id": "b", "score": 1.0}, {"id": "a", "score": 1.0}]
    result = select_high_score(records, retain_count=1)
    assert result["selected_ids"] == ["a"]


def test_offset_window_selects_low_score_window_after_offset():
    records = [
        {"id": "a", "score": 0.1},
        {"id": "b", "score": 0.2},
        {"id": "c", "score": 0.3},
        {"id": "d", "score": 0.4},
    ]
    result = select_offset_window(records, retain_count=2, offset_fraction=0.25)
    assert result["selected_ids"] == ["b", "c"]
    assert set(result["pruned_ids"]) == {"a", "d"}


def test_reject_duplicate_ids():
    try:
        select_high_score([{"id": "a", "score": 1.0}, {"id": "a", "score": 0.5}], retain_count=1)
    except ValueError as exc:
        assert "unique" in str(exc)
    else:
        raise AssertionError("duplicate ids were accepted")


if __name__ == "__main__":
    test_high_score_fraction_selection()
    test_tie_break_by_id()
    test_offset_window_selects_low_score_window_after_offset()
    test_reject_duplicate_ids()
    print("ok")
