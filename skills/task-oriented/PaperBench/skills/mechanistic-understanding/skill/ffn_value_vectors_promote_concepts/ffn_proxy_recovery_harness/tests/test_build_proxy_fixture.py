from build_proxy_fixture import build_fixture

def test_fixture_has_three_concepts():
    f=build_fixture()
    assert set(f['lexicon'])=={'animal','color','food'}
    assert len(f['vocab'])==5
