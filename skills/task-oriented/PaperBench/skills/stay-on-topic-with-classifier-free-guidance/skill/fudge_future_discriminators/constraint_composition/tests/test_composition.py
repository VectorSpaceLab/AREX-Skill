import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from composition import compose_constraints

def test_lambda_over_n_composition():
    probs={'ship': {'earth':0.5, 'orbit':0.25}}
    out=compose_constraints(probs, ['earth','orbit'], lambda_value=4)
    expected=2*(math.log(0.5)+math.log(0.25))
    assert abs(out['scores']['ship']-expected) < 1e-9

def test_missing_score_raises():
    try:
        compose_constraints({'x': {'a':0.5}}, ['a','b'])
        raise AssertionError('missing score not detected')
    except KeyError:
        pass
