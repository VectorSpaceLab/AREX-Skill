from metrics import intra_cluster_distance, correspondence_correlation, rank_agreement


def test_duplicate_samples_have_zero_cluster_diversity():
    result = intra_cluster_distance([[0,0], [0,0]], [[0,0]])
    assert result['average_intra_cluster_distance'] == 0.0


def test_correspondence_correlation_is_high_for_scaled_vectors():
    source = [[1,0], [0,1], [1,1]]
    adapted = [[2,0], [0,2], [2,2]]
    assert correspondence_correlation(source, adapted) > 0.99
    assert rank_agreement(source, adapted) == 1.0
