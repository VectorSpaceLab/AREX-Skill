def _predict(full_logprobs, short_logprobs, alpha):
    scores = [float(f) + float(alpha) * float(s) for f, s in zip(full_logprobs, short_logprobs)]
    best = max(range(len(scores)), key=lambda i: (scores[i], -i))
    return best


def accuracy_for_alpha(examples, alpha):
    correct=0
    preds=[]
    for ex in examples:
        p=_predict(ex["full_logprobs"], ex["short_logprobs"], alpha)
        preds.append(p)
        correct += int(p == int(ex["label"]))
    return correct/len(examples), preds


def select_alpha(examples, alpha_grid):
    if not examples:
        raise ValueError("examples must be non-empty")
    curve=[]
    for a in alpha_grid:
        acc, preds=accuracy_for_alpha(examples, float(a))
        curve.append({"alpha": float(a), "accuracy": acc, "predictions": preds})
    best=max(curve, key=lambda r: (r["accuracy"], -abs(r["alpha"]), -r["alpha"]))
    return {"best_alpha": best["alpha"], "best_accuracy": best["accuracy"], "curve": curve, "tie_break":"max accuracy, then smallest |alpha|, then smaller alpha"}
