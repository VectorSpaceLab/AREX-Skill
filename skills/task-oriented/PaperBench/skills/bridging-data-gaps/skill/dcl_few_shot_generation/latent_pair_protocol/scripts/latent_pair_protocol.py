import json


def _features(record):
    values = record.get("features")
    if not isinstance(values, list) or not values:
        raise ValueError("features must be a non-empty list")
    return [float(v) for v in values]


def build_latent_pair_batch(source_records, target_records, real_target_records):
    source = {}
    target = {}
    for record in source_records:
        latent = record.get("latent_id")
        if not latent or latent in source:
            raise ValueError("source latent ids must be present and unique")
        source[latent] = _features(record)
    for record in target_records:
        latent = record.get("latent_id")
        if not latent or latent in target:
            raise ValueError("target latent ids must be present and unique")
        target[latent] = _features(record)
    if set(source) != set(target):
        raise ValueError("source and target latent ids must match exactly")
    real_targets = [{"id": r.get("id", f"real_{i}"), "features": _features(r)} for i, r in enumerate(real_target_records)]
    if not real_targets:
        raise ValueError("at least one real target exemplar is required")
    pairs = []
    for latent in sorted(source):
        pairs.append({"latent_id": latent, "source_features": source[latent], "target_features": target[latent]})
    return {"pairs": pairs, "real_target_negatives": real_targets, "latent_count": len(pairs)}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("output_json")
    args = parser.parse_args()
    data = json.load(open(args.input_json, encoding="utf-8"))
    result = build_latent_pair_batch(data["source"], data["target"], data["real_targets"])
    json.dump(result, open(args.output_json, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    main()
