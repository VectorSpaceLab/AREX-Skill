from run_diayn_recovery import build_lineworld_item


def test_lineworld_item_declares_proxy_mechanism_fields():
    item = build_lineworld_item()
    assert item["dataset"] == "deterministic_three_skill_lineworld"
    assert item["is_resource_derived"] is False
    assert item["skill_targets"] == [-1.0, 0.0, 1.0]
    assert "skill-state discriminability" in item["rationale"]
