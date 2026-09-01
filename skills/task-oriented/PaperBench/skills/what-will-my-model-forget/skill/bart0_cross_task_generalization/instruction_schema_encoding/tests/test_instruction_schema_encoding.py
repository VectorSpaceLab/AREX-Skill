from instruction_encoding import encode_instruction

def sample():
    return {"input":"Fact: ice is cold", "output":"What is cold?", "instruction":{"prompt":"Write a question.","definition":"Generate a question answered by the fact.","things_to_avoid":"Do not copy the fact verbatim.","emphasis":"Ask one question.","positive_examples":[{"input":"Fact: birds fly","output":"What can fly?","reason":"asks about fact"}],"negative_examples":[{"input":"Fact: water boils","output":"water boils","reason":"not a question"}]}}

def test_full_encoding_uses_instruction_fields_without_target_leakage():
    out=encode_instruction(sample(), 'full')
    assert 'Definition:' in out['text']
    assert 'PositiveExample1' in out['text']
    assert out['target_leaked'] is False

def test_no_instruction_keeps_only_instance_contract():
    out=encode_instruction(sample(), 'none')
    assert out['fields_used'] == ['input']
    assert 'Definition:' not in out['text']
