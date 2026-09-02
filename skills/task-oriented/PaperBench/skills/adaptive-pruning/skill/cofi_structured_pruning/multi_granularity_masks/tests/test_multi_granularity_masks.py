
from cofi_masks import effective_units, estimate_active_parameters

def test_coarse_layer_dominates_fine_masks():
    eff=effective_units([1,0], [[1,1],[1,1]], [[1,0],[1,1]], [1,0,1])
    assert eff['heads'][0] == [1.0,1.0]
    assert eff['heads'][1] == [0.0,0.0]
    assert eff['intermediate'][1] == [0.0,0.0]

def test_active_parameter_estimate_counts_effective_units():
    eff=effective_units([1], [[1,0,1]], [[0.5,1]], [1,1])
    est=estimate_active_parameters(eff, head_size=10, intermediate_size_per_dim=2, hidden_size_per_dim=1)
    assert est['active_heads'] == 2
    assert est['active_intermediate_dims'] == 1.5
    assert est['active_parameters'] == 25
