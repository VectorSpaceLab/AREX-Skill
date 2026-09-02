from sense_tagger import tag_senses


def build_taxonomy():
    return {
        "synsets": [
            {"id": "bank.n.01", "lemmas": ["bank"], "pos": "n", "gloss": "financial institution money deposits", "relations": []},
            {"id": "bank.n.02", "lemmas": ["bank"], "pos": "n", "gloss": "sloping land beside a river", "relations": []},
            {"id": "river.n.01", "lemmas": ["river"], "pos": "n", "gloss": "natural stream of water", "relations": [{"type": "related", "target": "bank.n.02"}]},
        ]
    }


def test_context_selects_senses_and_records_unknown():
    records = [
        {"sentence_id": 0, "tokens": [
            {"surface": "bank", "lemma": "bank", "pos_hint": "n"},
            {"surface": "river", "lemma": "river", "pos_hint": "n"},
        ]},
        {"sentence_id": 1, "tokens": [
            {"surface": "unknownword", "lemma": "unknownword", "pos_hint": "n"},
        ]},
    ]
    tagged = tag_senses(records, build_taxonomy())
    bank = [t for t in tagged[0]["tagged_tokens"] if t["lemma"] == "bank"][0]
    assert bank["sense_id"] == "bank.n.02"
    unknown = tagged[1]["tagged_tokens"][0]
    assert unknown["reason"] == "no_wordnet_entry_for_lemma_pos"
