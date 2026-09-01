from preprocessor import preprocess_text, normalize_word

def test_collocation_before_morphology():
    records = preprocess_text('The nervous condition improved.', ['nervous condition'])
    assert records[0]['tokens'][1]['lemma'] == 'nervous_condition'
    assert records[0]['collocation_spans'][0]['text'] == 'nervous condition'
    assert normalize_word('conditions') == 'condition'


def test_ous_adjective_is_not_singularized():
    records = preprocess_text('A nervous student waited.', [])
    lemmas = [token['lemma'] for token in records[0]['tokens']]
    assert 'nervous' in lemmas
