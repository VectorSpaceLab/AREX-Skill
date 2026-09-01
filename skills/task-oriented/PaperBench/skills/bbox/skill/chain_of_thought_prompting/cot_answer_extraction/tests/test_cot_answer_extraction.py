from cot_answer_extraction import extract_answer


def test_numeric_extracts_final_answer_not_intermediate_number():
    result = extract_answer("Roger buys 2 * 3 = 6 balls. 5 + 6 = 11. The answer is 11.", "numeric")
    assert result.extracted_answer == "11"
    assert result.normalized_answer == "11"


def test_numeric_currency_and_comma_are_canonicalized():
    result = extract_answer("The subtotal is 1,200 and tax is 34. The answer is $1,234 dollars.", "numeric")
    assert result.normalized_answer == "1234"


def test_multiple_choice_letter():
    result = extract_answer("There are 401 three-digit numbers. The answer is (b).", "multiple_choice")
    assert result.normalized_answer == "b"


def test_yes_no_and_date():
    assert extract_answer("Thus it floats. So the answer is no.", "yes_no").normalized_answer == "no"
    assert extract_answer("Ten days ago was 05/23/1943. The answer is 05/23/1943.", "date").normalized_answer == "05/23/1943"


def test_symbolic_answer():
    result = extract_answer('The last letters are "y" and "a". So the answer is ya.', "symbolic")
    assert result.normalized_answer == "ya"
