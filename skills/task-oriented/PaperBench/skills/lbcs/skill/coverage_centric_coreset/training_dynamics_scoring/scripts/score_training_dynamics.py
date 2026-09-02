import argparse, json, math
from collections import defaultdict


def _check_probs(probabilities, num_classes):
    if len(probabilities) != num_classes:
        raise ValueError('probability vector length does not match num_classes')
    if any(p < 0 for p in probabilities):
        raise ValueError('probabilities must be non-negative')
    total = sum(probabilities)
    if total <= 0:
        raise ValueError('probabilities must have positive mass')
    return [p / total for p in probabilities]


def compute_scores(records, num_classes=None, max_el2n_epoch=10):
    if not records:
        raise ValueError('records must be non-empty')
    if num_classes is None:
        num_classes = len(records[0]['probabilities'])
    by_index = {}
    correctness = defaultdict(int)
    forgetting = defaultdict(int)
    last_correctness = defaultdict(int)
    accumulated_margin = defaultdict(float)
    el2n = defaultdict(float)
    for rec in sorted(records, key=lambda x: (x.get('epoch', 0), x['index'])):
        idx = int(rec['index'])
        label = int(rec['label'])
        probs = _check_probs([float(x) for x in rec['probabilities']], num_classes)
        if not 0 <= label < num_classes:
            raise ValueError('label out of range')
        if idx in by_index and by_index[idx] != label:
            raise ValueError('label changed for an index')
        by_index[idx] = label
        pred = max(range(num_classes), key=lambda i: probs[i])
        is_correct = int(pred == label)
        if last_correctness[idx] == 1 and is_correct == 0:
            forgetting[idx] += 1
        last_correctness[idx] = is_correct
        correctness[idx] += is_correct
        target_prob = probs[label]
        other_highest = max(probs[i] for i in range(num_classes) if i != label)
        accumulated_margin[idx] += target_prob - other_highest
        if int(rec.get('epoch', 0)) < max_el2n_epoch:
            el2n[idx] += math.sqrt(sum(((1.0 if i == label else 0.0) - probs[i]) ** 2 for i in range(num_classes)))
    indices = sorted(by_index)
    return {
        'indices': indices,
        'targets': [by_index[i] for i in indices],
        'correctness': [correctness[i] for i in indices],
        'forgetting': [forgetting[i] for i in indices],
        'last_correctness': [last_correctness[i] for i in indices],
        'accumulated_margin': [accumulated_margin[i] for i in indices],
        'el2n': [el2n[i] for i in indices],
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('input_json')
    p.add_argument('--output', required=True)
    p.add_argument('--num-classes', type=int, default=None)
    p.add_argument('--max-el2n-epoch', type=int, default=10)
    args = p.parse_args()
    records = json.load(open(args.input_json, encoding='utf-8'))
    result = compute_scores(records, args.num_classes, args.max_el2n_epoch)
    json.dump(result, open(args.output, 'w', encoding='utf-8'), indent=2)

if __name__ == '__main__':
    main()
