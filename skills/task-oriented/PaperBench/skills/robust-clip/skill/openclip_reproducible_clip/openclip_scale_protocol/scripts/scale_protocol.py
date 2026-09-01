import argparse
import json

REQUIRED = ("dataset", "model", "samples_seen", "gmac_per_sample")


def build_scale_table(records):
    output = []
    for index, record in enumerate(records):
        for field in REQUIRED:
            if field not in record:
                raise ValueError(f"record {index} missing {field}")
        samples_seen = float(record["samples_seen"])
        gmac_per_sample = float(record["gmac_per_sample"])
        if samples_seen <= 0 or gmac_per_sample <= 0:
            raise ValueError("samples_seen and gmac_per_sample must be positive")
        item = dict(record)
        item["total_compute"] = samples_seen * gmac_per_sample
        if "accuracy" in item:
            item["classification_error"] = 100.0 - float(item["accuracy"])
        if "recall_at_5" in item:
            item["retrieval_error"] = 100.0 - float(item["recall_at_5"])
        output.append(item)
    return {"schema_version": 1, "records": output, "record_count": len(output)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.input, "r", encoding="utf-8") as handle:
        records = json.load(handle)
    result = build_scale_table(records)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)

if __name__ == "__main__":
    main()
