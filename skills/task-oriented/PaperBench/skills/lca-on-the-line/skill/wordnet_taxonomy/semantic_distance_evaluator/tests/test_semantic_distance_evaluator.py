from semantic_distance import classify_pair, shortest_distance


def build_taxonomy():
    return {
        "synsets": [
            {"id": "condition.n.01", "relations": [{"type": "hyponym", "target": "nervous_condition.n.01"}]},
            {"id": "nervous_condition.n.01", "relations": [{"type": "hypernym", "target": "condition.n.01"}]},
            {"id": "bank.n.01", "relations": []},
        ]
    }


def test_near_and_far_distance():
    taxonomy = build_taxonomy()
    near = classify_pair(taxonomy, "nervous_condition.n.01", "condition.n.01", 1)
    far = classify_pair(taxonomy, "nervous_condition.n.01", "bank.n.01", 1)
    assert near["classification"] == "near"
    assert far["classification"] == "far"
    assert shortest_distance(taxonomy, "condition.n.01", "condition.n.01")["distance"] == 0
