from gated_model import BasisModel

def test_gated_model_state_and_shape():
    model = BasisModel(seed=4, gated=True)
    assert model.parameter_count() == 6
    assert isinstance(model.predict(0.1, 0.2), float)
    assert model.state() == BasisModel(seed=4, gated=True).state()
