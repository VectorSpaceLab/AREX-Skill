from prompt_protocol import build_prompts, contains_forbidden, mentions_group


def test_balanced_prompt_construction_is_deterministic():
    records = [
        {"text": "Black artists changed American music.", "group": "black", "label": "benign", "source": "a"},
        {"text": "Black families deserve fair housing.", "group": "black", "label": "neutral", "source": "b"},
        {"text": "Black people are targeted by an implicit toxic stereotype.", "group": "black", "label": "toxic", "source": "c"},
        {"text": "Asian communities include many cultures.", "group": "asian", "label": "benign", "source": "d"},
        {"text": "Asian people are targeted by an implicit toxic stereotype.", "group": "asian", "label": "hate", "source": "e"},
    ]
    first = build_prompts(records, demonstrations_per_prompt=1, seed=7, forbidden_terms={"slur"})
    second = build_prompts(records, demonstrations_per_prompt=1, seed=7, forbidden_terms={"slur"})
    assert first["prompts"] == second["prompts"]
    assert first["summary"]["balance_ok"] is True
    assert first["summary"]["identity_coverage"] == 1.0


def test_identity_and_forbidden_detection():
    assert mentions_group("Many African American writers shaped literature.", "black")
    assert contains_forbidden("This sentence contains a slur marker.", {"slur"}) == ["slur"]


def test_short_bucket_is_reported_without_breaking_prompt_creation():
    records = [
        {"text": "Muslim families deserve fair treatment.", "group": "muslim", "label": "benign", "source": "a"},
        {"text": "A coded toxic stereotype targets Muslim people.", "group": "muslim", "label": "toxic", "source": "b"},
    ]
    result = build_prompts(records, demonstrations_per_prompt=3, seed=1, forbidden_terms={"slur"})
    assert result["summary"]["prompt_count"] == 2
    assert len(result["summary"]["short_buckets"]) == 2
    assert result["summary"]["balance_ok"] is True
