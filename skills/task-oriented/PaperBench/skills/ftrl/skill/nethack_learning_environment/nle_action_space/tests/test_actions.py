from actions import canonicalize_action

def test_reduced_action_validity():
    assert canonicalize_action("eat")["valid"] is True
    assert canonicalize_action("read")["valid"] is False
    assert canonicalize_action("read")["invalid_penalty"] == -0.001
