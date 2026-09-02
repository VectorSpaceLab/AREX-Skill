
import math

def softmax(logits):
    max_logit = max(logits)
    exps = [math.exp(x - max_logit) for x in logits]
    total = sum(exps)
    return [x / total for x in exps]

def entropy(logits):
    probs = softmax(logits)
    return -sum(p * math.log(max(p, 1e-12)) for p in probs)

def default_margin(class_count):
    return 0.4 * math.log(class_count)

def filter_reliable(logits_batch, class_count=None, margin=None):
    if not logits_batch:
        return {'entropies': [], 'selected_indices': [], 'mean_entropy': None, 'margin': margin}
    if class_count is None:
        class_count = len(logits_batch[0])
    if margin is None:
        margin = default_margin(class_count)
    entropies = [entropy(row) for row in logits_batch]
    selected = [i for i, value in enumerate(entropies) if value < margin]
    mean_entropy = sum(entropies[i] for i in selected) / len(selected) if selected else None
    return {'entropies': entropies, 'selected_indices': selected, 'mean_entropy': mean_entropy, 'margin': margin}
