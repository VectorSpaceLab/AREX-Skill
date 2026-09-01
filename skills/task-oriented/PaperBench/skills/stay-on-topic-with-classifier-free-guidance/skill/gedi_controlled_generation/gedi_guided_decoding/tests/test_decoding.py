import math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from gedi_decode import guided_distribution

tokens = ['boring', 'wonderful', 'plain']
base = [math.log(0.7), math.log(0.2), math.log(0.1)]
post = [0.1, 0.95, 0.5]
out = guided_distribution(tokens, base, post, omega=4.0, rho=0.2)
assert out['selected_token'] == 'wonderful'
assert out['keep_mask']['wonderful'] is True
assert sum(out['filtered_probabilities'].values()) > 0.999999

out_all = guided_distribution(tokens, base, post, omega=0.0, rho=1.0)
assert all(out_all['keep_mask'].values())
assert out_all['selected_token'] == 'boring'

try:
    guided_distribution(['a'], [0.0, 1.0], [0.5])
    raise AssertionError('expected shape error')
except ValueError:
    pass

print('gedi_guided_decoding tests passed')
