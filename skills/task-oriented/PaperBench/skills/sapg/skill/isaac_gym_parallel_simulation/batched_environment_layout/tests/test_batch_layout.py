from batch_layout import apply_resets, create_layout, validate_layout


def test_layout_isolation_and_reset():
    layout = create_layout(4, ['position', 'velocity'])
    layout['states']['position'] = [1.0, 2.0, 3.0, 4.0]
    apply_resets(layout, [False, True, False, True], reset_value=-1.0)
    assert validate_layout(layout)
    assert layout['states']['position'] == [1.0, -1.0, 3.0, -1.0]
    assert layout['states']['velocity'] == [0.0, -1.0, 0.0, -1.0]
