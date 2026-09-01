from dataclasses import dataclass


def normalize_ws(text):
    return " ".join(str(text).split())


def build_record(example):
    required = ["premise", "prompt", "candidates", "label"]
    for key in required:
        if key not in example:
            raise ValueError(f"missing {key}")
    premise = normalize_ws(example["premise"])
    prompt = normalize_ws(example["prompt"])
    candidates = list(example["candidates"])
    label = int(example["label"])
    if not candidates:
        raise ValueError("candidates must be non-empty")
    if label < 0 or label >= len(candidates):
        raise ValueError("label out of range")
    return {"full_context": (premise + " " + prompt).strip(), "premise_free_context": prompt, "candidates": candidates, "label": label}


def validate_record(record):
    if not record.get("full_context") or not record.get("premise_free_context"):
        return False
    if record["full_context"] == record["premise_free_context"]:
        return False
    return 0 <= int(record["label"]) < len(record.get("candidates", []))
