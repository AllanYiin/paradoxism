from paradoxism.utils.docstring_utils import parse_docstring


def test_parse_docstring_google():
    doc = """
    Detect emotions in a given sentence.

    Args:
        sentence (str): The sentence to analyze.

    Returns:
        dict: result.
    """
    result = parse_docstring(doc, style="google")
    assert result["input_args"][0]["arg_name"] == "sentence"
    assert result["input_args"][0]["arg_type"] == "str"
    assert result["return"][0]["return_name"] == "return"
