from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from task_protocol import data_item_from_protocol, synthetic_two_task_protocol, validate_no_rehearsal


def test_protocol_is_deterministic_and_valid():
    first = synthetic_two_task_protocol()
    second = synthetic_two_task_protocol()
    assert first == second
    validate_no_rehearsal(first)
    assert first["task_order"] == ["task_a", "task_b"]
    assert first["train_task"] == "task_b"


def test_data_item_records_proxy_boundary():
    protocol = synthetic_two_task_protocol()
    item = data_item_from_protocol(protocol)
    assert item["is_resource_derived"] is False
    assert item["sample_count"] == 16
    assert item["train_task"] == "task_b"
