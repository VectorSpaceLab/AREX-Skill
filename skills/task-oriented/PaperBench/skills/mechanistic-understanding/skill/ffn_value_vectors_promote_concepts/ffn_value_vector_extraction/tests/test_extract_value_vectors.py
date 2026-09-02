from extract_value_vectors import extract_from_state_dict, extract_from_matrix

def test_columns_as_neurons_for_c_proj():
    out = extract_from_state_dict({'h.0.mlp.c_proj.weight': [[1,0,2],[0,1,2]]})
    assert len(out['vectors']) == 3
    assert out['vectors'][0]['vector'] == [1.0, 0.0]
    assert out['vectors'][2]['vector'] == [2.0, 2.0]

def test_rows_orientation_direct_matrix():
    out = extract_from_matrix([[1,2],[3,4]], orientation='neurons_by_rows')
    assert out['residual_dim'] == 2
    assert out['vectors'][1]['vector'] == [3.0, 4.0]
