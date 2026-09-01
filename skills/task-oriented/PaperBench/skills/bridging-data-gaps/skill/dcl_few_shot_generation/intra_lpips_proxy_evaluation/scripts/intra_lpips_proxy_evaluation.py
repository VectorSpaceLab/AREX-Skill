import json, math


def dist(a,b):
    return math.sqrt(sum((float(x)-float(y))**2 for x,y in zip(a,b)))


def intra_cluster_proxy(generated, targets):
    clusters = {str(i): [] for i in range(len(targets))}
    for item in generated:
        feat = item["features"]
        nearest = min(range(len(targets)), key=lambda i: dist(feat, targets[i]["features"]))
        clusters[str(nearest)].append(feat)
    distances = []
    counts = {}
    for key, feats in clusters.items():
        count = 0
        for i in range(len(feats)):
            for j in range(i+1, len(feats)):
                distances.append(dist(feats[i], feats[j])); count += 1
        counts[key] = count
    return {"intra_cluster_proxy": sum(distances)/len(distances) if distances else 0.0, "pair_counts": counts, "cluster_count": len(clusters)}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("output_json")
    args = parser.parse_args()
    data = json.load(open(args.input_json, encoding="utf-8"))
    json.dump(intra_cluster_proxy(data["generated"], data["targets"]), open(args.output_json, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    main()
