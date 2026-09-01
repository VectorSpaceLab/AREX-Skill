from lexical_schema import build_tiny_taxonomy, validate_taxonomy, lemma_index

def test_inventory_and_index():
    taxonomy = build_tiny_taxonomy()
    counts = validate_taxonomy(taxonomy)
    assert counts['synsets'] >= 5
    assert counts['semantic_pointers'] >= 3
    index = lemma_index(taxonomy)
    assert ('bank', 'n') in index
    assert len(index[('bank', 'n')]) == 2


def test_duplicate_normalized_lemmas_do_not_duplicate_candidates():
    taxonomy = build_tiny_taxonomy()
    index = lemma_index(taxonomy)
    candidates = index[("nervous_condition", "n")]
    assert [c["id"] for c in candidates] == ["nervous_condition.n.01"]
