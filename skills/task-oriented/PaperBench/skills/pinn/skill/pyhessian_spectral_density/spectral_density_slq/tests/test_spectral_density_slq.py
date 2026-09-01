from slq_density import lanczos_tridiagonal, two_by_two_density

def test_lanczos_density_recovers_two_point_support():
    def hvp(v): return [5.0*v[0], 1.0*v[1]]
    tri = lanczos_tridiagonal(hvp, [1.0, 1.0], 2)
    density = two_by_two_density(tri)
    vals = sorted(round(x, 6) for x in density['eigenvalues'])
    assert vals == [1.0, 5.0]
    assert abs(sum(density['weights']) - 1.0) < 1e-9

from slq_density import density_contract

def test_density_contract_requires_normalized_weights():
    assert density_contract({'eigenvalues': [1.0, 2.0], 'weights': [0.25, 0.75]})
    assert not density_contract({'eigenvalues': [1.0], 'weights': [0.5]})
