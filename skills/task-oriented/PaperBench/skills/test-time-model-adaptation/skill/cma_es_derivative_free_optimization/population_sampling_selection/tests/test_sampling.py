import random
from cmaes_sampling import sample_and_select, dot

def test_sampling_returns_sorted_records_and_mean_step():
    params = {'lambda': 6, 'mu': 3, 'weights': [0.6, 0.3, 0.1], 'cm': 1.0}
    rng = random.Random(3)
    result = sample_and_select([2.0, 0.0], 0.5, [[1.0,0.0],[0.0,1.0]], params, lambda x: dot(x, x), rng)
    fitnesses = [r['fitness'] for r in result['records']]
    assert fitnesses == sorted(fitnesses)
    assert len(result['selected_y']) == 3
    assert len(result['new_mean']) == 2
    assert result['best_fitness'] == fitnesses[0]
