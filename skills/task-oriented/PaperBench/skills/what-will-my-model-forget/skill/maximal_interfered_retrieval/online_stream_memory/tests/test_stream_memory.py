from stream_memory import ReplayMemory, compute_forgetting, make_stream


def test_memory_capacity_and_candidates_are_bounded():
    memory = ReplayMemory(capacity=3, seed=7)
    memory.add_many({"example_id": str(i), "label": i % 2} for i in range(8))
    assert len(memory.items) == 3
    assert len(memory.candidates(2)) == 2
    assert len(memory.candidates(20)) == 3


def test_zero_capacity_and_stream_fields():
    memory = ReplayMemory(capacity=0)
    stream = make_stream([[([1.0, 0.0], 0)], [([0.0, 1.0], 1)]])
    memory.add_many(stream)
    assert memory.items == []
    assert stream[0]["task_id"] == 0
    assert stream[1]["task_id"] == 1


def test_forgetting_summary():
    summary = compute_forgetting({"0": [0.8, 0.6], "1": [0.4, 0.7]})
    assert abs(summary["average_forgetting"] - 0.1) < 1e-9
    assert abs(summary["per_task"]["0"]["forgetting"] - 0.2) < 1e-9
