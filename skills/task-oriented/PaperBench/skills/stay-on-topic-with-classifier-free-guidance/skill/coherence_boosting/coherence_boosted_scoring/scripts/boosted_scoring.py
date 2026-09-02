import math


def boosted_scores(full_logprobs, short_logprobs, alpha):
    if len(full_logprobs) != len(short_logprobs) or not full_logprobs:
        raise ValueError("likelihood lists must be non-empty and equal length")
    out=[]
    for f,s in zip(full_logprobs, short_logprobs):
        f=float(f); s=float(s)
        if not (math.isfinite(f) and math.isfinite(s)):
            raise ValueError("log likelihoods must be finite")
        out.append(f + float(alpha)*s)
    return out


def predict(full_logprobs, short_logprobs, alpha):
    scores=boosted_scores(full_logprobs, short_logprobs, alpha)
    best=max(range(len(scores)), key=lambda i: (scores[i], -i))
    sorted_scores=sorted(scores, reverse=True)
    margin=sorted_scores[0]-sorted_scores[1] if len(sorted_scores)>1 else 0.0
    return {"prediction": best, "scores": scores, "margin": margin, "alpha": float(alpha)}
