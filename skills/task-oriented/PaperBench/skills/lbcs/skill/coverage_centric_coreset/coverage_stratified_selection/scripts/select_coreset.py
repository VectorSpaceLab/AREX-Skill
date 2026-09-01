import argparse, json, random
from collections import Counter


def _allocate(total, counts):
    order = sorted(range(len(counts)), key=lambda i: counts[i])
    budgets = [0] * len(counts)
    remaining = int(total)
    for pos, bin_idx in enumerate(order):
        rest = len(order) - pos
        avg = remaining // rest if rest else 0
        cur = min(counts[bin_idx], avg)
        budgets[bin_idx] = cur
        remaining -= cur
    pos = 0
    while remaining > 0 and any(counts[i] > budgets[i] for i in range(len(counts))):
        i = order[pos % len(order)]
        if counts[i] > budgets[i]:
            budgets[i] += 1
            remaining -= 1
        pos += 1
    return budgets


def monotonic_selection(score_table, key, coreset_ratio, descending=False):
    n = len(score_table[key])
    k = max(1, int(round(n * coreset_ratio)))
    indices = score_table.get('indices', list(range(n)))
    order = sorted(range(n), key=lambda i: (score_table[key][i], indices[i]), reverse=descending)
    return [indices[i] for i in order[:k]]


def select_coverage_coreset(score_table, key='accumulated_margin', coreset_ratio=0.1, mis_ratio=0.3, strata=50, seed=0):
    scores = [float(x) for x in score_table[key]]
    indices = list(score_table.get('indices', range(len(scores))))
    targets = list(score_table.get('targets', [0] * len(scores)))
    if not scores:
        raise ValueError('score table is empty')
    if not (0 < coreset_ratio <= 1):
        raise ValueError('coreset_ratio must be in (0, 1]')
    if not (0 <= mis_ratio < 1):
        raise ValueError('mis_ratio must be in [0, 1)')
    if strata <= 0:
        raise ValueError('strata must be positive')
    n = len(scores)
    remove_n = int(n * mis_ratio)
    margin = score_table.get('accumulated_margin', scores)
    remove_order = sorted(range(n), key=lambda i: (margin[i], indices[i]))
    removed = set(remove_order[:remove_n])
    remaining = [i for i in range(n) if i not in removed]
    coreset_n = max(1, int(round(n * coreset_ratio)))
    lo, hi = min(scores[i] for i in remaining), max(scores[i] for i in remaining)
    width = (hi - lo) / strata if hi > lo else 1.0
    bins = [[] for _ in range(strata)]
    for i in remaining:
        b = min(strata - 1, int((scores[i] - lo) / width)) if hi > lo else 0
        bins[b].append(i)
    counts = [len(b) for b in bins]
    budgets = _allocate(min(coreset_n, len(remaining)), counts)
    rng = random.Random(seed)
    selected_internal = []
    for b, budget in enumerate(budgets):
        pool = bins[b][:]
        rng.shuffle(pool)
        selected_internal.extend(sorted(pool[:budget], key=lambda i: indices[i]))
    selected = [indices[i] for i in selected_internal]
    represented_bins = [b for b, pool in enumerate(bins) if any(i in selected_internal for i in pool)]
    class_counts = dict(Counter(str(targets[i]) for i in selected_internal))
    return {
        'selected_indices': selected,
        'removed_indices': [indices[i] for i in remove_order[:remove_n]],
        'strata_budgets': budgets,
        'represented_bins': represented_bins,
        'class_counts': class_counts,
        'coreset_size': len(selected),
        'available_after_filter': len(remaining),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('score_json')
    p.add_argument('--output', required=True)
    p.add_argument('--key', default='accumulated_margin')
    p.add_argument('--coreset-ratio', type=float, default=0.1)
    p.add_argument('--mis-ratio', type=float, default=0.3)
    p.add_argument('--strata', type=int, default=50)
    p.add_argument('--seed', type=int, default=0)
    args = p.parse_args()
    table = json.load(open(args.score_json, encoding='utf-8'))
    result = select_coverage_coreset(table, args.key, args.coreset_ratio, args.mis_ratio, args.strata, args.seed)
    json.dump(result, open(args.output, 'w', encoding='utf-8'), indent=2)

if __name__ == '__main__':
    main()
