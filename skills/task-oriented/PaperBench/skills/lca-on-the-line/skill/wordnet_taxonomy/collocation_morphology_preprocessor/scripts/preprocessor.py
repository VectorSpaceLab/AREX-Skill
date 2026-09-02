from __future__ import annotations

import re


def normalize_word(word):
    token = re.sub(r"[^A-Za-z_ ]", "", word).lower().replace(" ", "_")
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("ing") and len(token) > 5:
        stem = token[:-3]
        if len(stem) >= 2 and stem[-1] == stem[-2]:
            stem = stem[:-1]
        return stem
    if token.endswith("ed") and len(token) > 4:
        return token[:-2]
    if token.endswith("s") and len(token) > 3 and not token.endswith(("ss", "ous")):
        return token[:-1]
    return token


def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def preprocess_text(text, collocations):
    normalized_collocations = sorted({c.lower().replace("_", " ") for c in collocations}, key=lambda c: len(c.split()), reverse=True)
    records = []
    for sent_id, sentence in enumerate(split_sentences(text)):
        clean = re.sub(r"[^A-Za-z\s]", " ", sentence).lower()
        words = clean.split()
        tokens = []
        spans = []
        i = 0
        while i < len(words):
            matched = None
            for collocation in normalized_collocations:
                parts = collocation.split()
                if words[i:i+len(parts)] == parts:
                    matched = parts
                    break
            if matched:
                surface = " ".join(matched)
                tokens.append({"surface": surface, "lemma": normalize_word(surface), "pos_hint": "n"})
                spans.append({"start": i, "end": i + len(matched), "text": surface})
                i += len(matched)
            else:
                word = words[i]
                lemma = normalize_word(word)
                pos = "a" if lemma in {"nervous", "calm"} else "n"
                tokens.append({"surface": word, "lemma": lemma, "pos_hint": pos})
                i += 1
        records.append({"sentence_id": sent_id, "text": sentence, "tokens": tokens, "collocation_spans": spans})
    return records
