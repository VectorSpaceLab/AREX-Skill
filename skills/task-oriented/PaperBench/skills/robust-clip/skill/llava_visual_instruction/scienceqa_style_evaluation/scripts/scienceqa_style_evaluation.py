import re
import string


def normalize(text):
    return " ".join(str(text).lower().translate(str.maketrans("", "", string.punctuation)).split())


def canonicalize(raw_answer, choices=None):
    text = str(raw_answer).strip()
    explicit = re.search(r"(?:answer\s+is|option|choice)\s*[:\-]?\s*([A-E])\b", text, re.IGNORECASE)
    if explicit:
        return explicit.group(1).upper()
    bare = re.fullmatch(r"\s*([A-E])\s*[\.)]?\s*", text, re.IGNORECASE)
    if bare:
        return bare.group(1).upper()
    if choices:
        normalized_text = normalize(text)
        for key, value in choices.items():
            normalized_value = normalize(value)
            if normalized_value and (normalized_value in normalized_text or normalized_text in normalized_value):
                return key.upper()
    return normalize(text)


def evaluate_predictions(records):
    details = []
    correct = 0
    for rec in records:
        pred = canonicalize(rec.get("raw_answer", ""), rec.get("choices"))
        label_raw = str(rec.get("label", ""))
        label = label_raw.upper() if len(label_raw) == 1 else normalize(label_raw)
        ok = pred == label
        correct += int(ok)
        details.append({"id": rec.get("id"), "raw_answer": rec.get("raw_answer"), "prediction": pred, "label": label, "correct": ok})
    return {"accuracy": correct / len(records) if records else 0.0, "count": len(records), "details": details}
