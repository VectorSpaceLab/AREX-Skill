from anchor_patch import route_latents


def test_routes_exact_and_far_samples():
    result = route_latents([[0,0], [0.03,0.04], [2,2]], [[0,0]], 0.05)
    assert [r['route'] for r in result['routes']] == ['image', 'image', 'patch']
    assert result['counts'] == {'image': 2, 'patch': 1}


def test_threshold_boundary_is_image_route():
    result = route_latents([[0.05, 0.0]], [[0.0, 0.0]], 0.05)
    assert result['routes'][0]['route'] == 'image'
