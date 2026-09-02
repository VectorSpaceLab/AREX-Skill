from __future__ import annotations

REQUIRED_FIELDS = {"image_id", "caption", "class_name", "image_features", "text_features"}

def validate_paired_records(records):
    if not records:
        raise ValueError("records must be non-empty")
    seen = set()
    image_dim = text_dim = None
    normalized = []
    for idx, record in enumerate(records):
        missing = REQUIRED_FIELDS - set(record)
        if missing:
            raise ValueError(f"record {idx} missing fields: {sorted(missing)}")
        image_id = str(record["image_id"])
        if image_id in seen:
            raise ValueError(f"duplicate image_id: {image_id}")
        seen.add(image_id)
        image = [float(x) for x in record["image_features"]]
        text = [float(x) for x in record["text_features"]]
        if not image or not text:
            raise ValueError("features must be non-empty")
        if len(image) != len(text):
            raise ValueError("image/text feature dimensions must match")
        image_dim = image_dim or len(image)
        text_dim = text_dim or len(text)
        if len(image) != image_dim or len(text) != text_dim:
            raise ValueError("all feature dimensions must be consistent")
        caption = str(record["caption"]).strip()
        class_name = str(record["class_name"]).strip()
        if not caption or not class_name:
            raise ValueError("caption and class_name must be non-empty")
        normalized.append({"image_id": image_id, "caption": caption, "class_name": class_name, "image_features": image, "text_features": text})
    return {"records": normalized, "labels": list(range(len(normalized))), "feature_dim": image_dim}
