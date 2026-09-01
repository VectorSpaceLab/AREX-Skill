from input_transform import transform

def test_unmasked_theta_does_not_change_padding_coordinate():
    y=transform([0.0],3,[0,0,1],[99.0,88.0,0.25])
    assert y == [0.0,0.0,0.25]
