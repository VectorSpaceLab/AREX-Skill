import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from gedi_multiclass import build_control_pairs

out = build_control_pairs('Science', 'A rover landed on Mars.', seen_labels=['world','sports','business','science'])
assert out['control_passes'] == 2
assert out['positive_sequence'].startswith('true Science ')
assert out['negative_sequence'].startswith('false Science ')
assert out['seen_label'] is True

zero = build_control_pairs('climate', 'In a shocking finding', seen_labels=['world','sports','business','science'])
assert zero['zero_shot_candidate'] is True
assert zero['control_passes'] == 2

try:
    build_control_pairs('   ', 'text')
    raise AssertionError('expected label error')
except ValueError:
    pass
print('gedi_multiclass_control tests passed')
