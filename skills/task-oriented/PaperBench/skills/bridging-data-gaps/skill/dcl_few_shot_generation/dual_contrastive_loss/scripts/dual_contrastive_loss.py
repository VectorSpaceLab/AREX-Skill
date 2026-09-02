import json, math


def dot(a, b):
    return sum(float(x)*float(y) for x, y in zip(a, b))


def dcl_loss(batch, temperature=0.2, real_negative_weight=1.0):
    pairs = batch["pairs"]
    reals = batch.get("real_target_negatives", [])
    losses = []
    diagnostics = []
    for i, pair in enumerate(pairs):
        source = pair["source_features"]
        positive = pair["target_features"]
        pos_logit = dot(source, positive) / temperature
        logits = [pos_logit]
        kinds = ["positive"]
        for j, other in enumerate(pairs):
            if i != j:
                logits.append(dot(source, other["target_features"]) / temperature)
                kinds.append("generated_negative")
        for real in reals:
            logits.append(real_negative_weight * dot(source, real["features"]) / temperature)
            kinds.append("real_target_negative")
        max_logit = max(logits)
        denom = sum(math.exp(v - max_logit) for v in logits)
        loss = -(pos_logit - max_logit - math.log(denom))
        losses.append(loss)
        diagnostics.append({"latent_id": pair["latent_id"], "positive_logit": pos_logit, "negative_kinds": kinds[1:]})
    return {"loss": sum(losses)/len(losses), "per_pair": diagnostics, "mechanism_checks": {"same_latent_positives_used": True, "generated_negatives_used": len(pairs) > 1, "real_target_negatives_used": bool(reals)}}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("batch_json")
    parser.add_argument("output_json")
    parser.add_argument("--temperature", type=float, default=0.2)
    args = parser.parse_args()
    batch = json.load(open(args.batch_json, encoding="utf-8"))
    json.dump(dcl_loss(batch, args.temperature), open(args.output_json, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    main()
