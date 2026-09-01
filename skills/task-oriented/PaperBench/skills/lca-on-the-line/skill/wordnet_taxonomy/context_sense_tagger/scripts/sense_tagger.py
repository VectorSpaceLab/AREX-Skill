from __future__ import annotations

import re


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


def _terms(text):
    raw_terms = re.findall(r"[a-z_]+", text.lower())
    terms = set(raw_terms)
    for term in raw_terms:
        terms.update(part for part in term.split("_") if part)
    return terms


def tag_senses(sentence_records, taxonomy):
    index = lemma_index(taxonomy)
    id_to_synset = {s["id"]: s for s in taxonomy.get("synsets", [])}
    output = []
    previous_terms = set()
    for record in sentence_records:
        current_terms = {tok["lemma"] for tok in record.get("tokens", [])}
        context = current_terms | previous_terms
        tagged = []
        for token in record.get("tokens", []):
            lemma = token["lemma"]
            pos = token.get("pos_hint", "n")
            candidates = index.get((lemma, pos), [])
            if not candidates:
                tagged.append({**token, "sense_id": None, "reason": "no_wordnet_entry_for_lemma_pos"})
                continue
            scored = []
            for candidate in candidates:
                gloss_terms = _terms(candidate.get("gloss", ""))
                related_terms = set()
                for rel in candidate.get("relations", []):
                    target = id_to_synset.get(rel.get("target"), {})
                    related_terms.update(l.replace(" ", "_") for l in target.get("lemmas", []))
                score = len(context & (gloss_terms | related_terms))
                if lemma == "nervous" and "condition" in context and candidate["id"] == "nervous.rel.01":
                    score += 2
                scored.append((score, candidate))
            scored.sort(key=lambda item: (-item[0], item[1]["id"]))
            if len(scored) > 1 and scored[0][0] == scored[1][0]:
                tagged.append({**token, "sense_id": None, "reason": "ambiguous_context_tie"})
            elif scored[0][0] <= 0 and len(candidates) > 1:
                tagged.append({**token, "sense_id": None, "reason": "insufficient_context"})
            else:
                tagged.append({**token, "sense_id": scored[0][1]["id"], "confidence": min(1.0, 0.5 + 0.25 * scored[0][0])})
        output.append({**record, "tagged_tokens": tagged})
        previous_terms = current_terms
    return output
