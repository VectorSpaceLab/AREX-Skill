from protocol import evaluate_sequence

def logits(x): return [1-x[0], x[0], 0.0]

def test_sequence_filters_remaining_examples():
    examples=[[0.1],[0.2],[0.8]]; labels=[0,0,1]
    def attack1(xs,ys): return [[0.9] if i==0 else x for i,x in enumerate(xs)]
    def attack2(xs,ys): return [[0.9] if y == 0 else [0.1] for y in ys]
    out=evaluate_sequence(logits, examples, labels, [('a1',attack1),('a2',attack2)])
    assert out['per_attack'][0]['evaluated'] == 3
    assert out['per_attack'][1]['evaluated'] == 2
    assert out['robust_accuracy'] == 0.0
