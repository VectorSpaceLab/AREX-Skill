import math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from gedi_posterior import binary_desired_posterior, gedi_posteriors

p = binary_desired_posterior(-2.0, -4.0, length=2)
assert abs(p - (1/(1+math.exp(-1.0)))) < 1e-9

p_bias = binary_desired_posterior(-2.0, -4.0, length=2, desired_bias=-1.0)
assert p_bias < p

out = gedi_posteriors({'a': -10000.0, 'b': -9990.0}, 10)
assert abs(sum(out['posteriors'].values()) - 1.0) < 1e-12
assert out['posteriors']['b'] > out['posteriors']['a']

try:
    gedi_posteriors({'a': -1.0}, 0)
    raise AssertionError('expected length error')
except ValueError:
    pass

print('gedi_posterior tests passed')
