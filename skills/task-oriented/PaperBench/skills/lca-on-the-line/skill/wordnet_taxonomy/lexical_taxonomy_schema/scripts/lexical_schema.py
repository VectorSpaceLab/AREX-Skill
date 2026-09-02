from __future__ import annotations

from collections import Counter


def build_tiny_taxonomy():
    return {
        "synsets": [
            {"id": "condition.n.01", "lemmas": ["condition"], "pos": "n", "gloss": "state or medical condition", "relations": [{"type": "hyponym", "target": "nervous_condition.n.01"}]},
            {"id": "nervous_condition.n.01", "lemmas": ["nervous_condition", "nervous condition"], "pos": "n", "gloss": "condition of the nerves", "relations": [{"type": "hypernym", "target": "condition.n.01"}]},
            {"id": "nervous.a.01", "lemmas": ["nervous"], "pos": "a", "gloss": "anxious or uneasy student", "relations": [{"type": "antonym", "target": "calm.a.01"}]},
            {"id": "nervous.rel.01", "lemmas": ["nervous"], "pos": "a", "gloss": "relational adjective pertaining to nerves", "relations": [{"type": "pertains_to", "target": "nerve.n.01"}]},
            {"id": "nerve.n.01", "lemmas": ["nerve"], "pos": "n", "gloss": "bundle of fibers transmitting impulses", "relations": []},
            {"id": "bank.n.01", "lemmas": ["bank"], "pos": "n", "gloss": "financial institution money deposits", "relations": []},
            {"id": "bank.n.02", "lemmas": ["bank"], "pos": "n", "gloss": "sloping land beside a river", "relations": []},
            {"id": "river.n.01", "lemmas": ["river"], "pos": "n", "gloss": "natural stream of water", "relations": [{"type": "related", "target": "bank.n.02"}]},
            {"id": "calm.a.01", "lemmas": ["calm"], "pos": "a", "gloss": "not nervous", "relations": [{"type": "antonym", "target": "nervous.a.01"}]}
        ]
    }


def validate_taxonomy(taxonomy):
    synsets = taxonomy.get("synsets", [])
    ids = [s.get("id") for s in synsets]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate synset id")
    id_set = set(ids)
    strings = set()
    string_senses = []
    pointer_count = 0
    for synset in synsets:
        for lemma in synset.get("lemmas", []):
            strings.add(lemma)
            string_senses.append((lemma, synset["id"]))
        for relation in synset.get("relations", []):
            pointer_count += 1
            if relation.get("target") not in id_set:
                raise ValueError(f"dangling pointer: {synset['id']} -> {relation.get('target')}")
    return {"character_strings": len(strings), "synsets": len(synsets), "string_sense_combinations": len(string_senses), "semantic_pointers": pointer_count}


def lemma_index(taxonomy):
    index = {}
    seen = set()
    for synset in taxonomy.get("synsets", []):
        for lemma in synset.get("lemmas", []):
            key = (lemma.replace(" ", "_").lower(), synset.get("pos"))
            pair = (key, synset.get("id"))
            if pair in seen:
                continue
            seen.add(pair)
            index.setdefault(key, []).append(synset)
    return index
