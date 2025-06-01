from datetime import datetime
from paradoxism.ops.convert import force_cast


def test_force_cast_int_simple():
    response = "Some numbers: 12345 is the result."
    assert force_cast(response, "int") == 12345


def test_force_cast_int_with_commas():
    response = "Some numbers: 12,345 is the result."
    assert force_cast(response, "int") == 12345


def test_force_cast_float():
    response = "Value: 123.45 is the answer."
    assert force_cast(response, "float") == 123.45


def test_force_cast_float_scientific():
    response = "Value: 4e-5 is the answer."
    assert force_cast(response, "float") == 4e-05


def test_force_cast_date():
    response = "Today's date is 2023-10-01"
    assert force_cast(response, "date") == datetime(2023, 10, 1)


def test_force_cast_dict():
    response = "Here is a JSON: {\"key\": \"value\"}"
    assert force_cast(response, "dict") == {"key": "value"}


def test_force_cast_list():
    response = "List: [1, 2, 3, 4]"
    assert force_cast(response, "list") == [1, 2, 3, 4]


def test_force_cast_json():
    response = "Here is a JSON: {\"key\": \"value\"}"
    assert force_cast(response, "json") == {"key": "value"}


def test_force_cast_json_schema():
    response = "{\"name\": \"John\", \"age\": 30}"
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        "required": ["name", "age"],
    }
    assert force_cast(response, "json_schema", schema) == {"name": "John", "age": 30}


def test_force_cast_xml():
    response = "<person><name>John</name><age>30</age></person>"
    result = force_cast(response, "xml")
    assert result.tag == "person" and result.find("name").text == "John"


def test_force_cast_markdown():
    response = "# Title\nSome text."
    assert "<h1>Title</h1>" in force_cast(response, "markdown")


def test_force_cast_html():
    response = "&lt;div&gt;Some content&lt;/div&gt;"
    assert force_cast(response, "html") == "<div>Some content</div>"


def test_force_cast_invalid_json():
    response = "Invalid JSON: {key: value}"
    assert "Error" in force_cast(response, "json")


def test_force_cast_empty_string():
    assert force_cast("", "str") == ""


def test_force_cast_non_numeric_int():
    response = "This is not a number: abc"
    assert "Error" in force_cast(response, "int")


def test_force_cast_clean_json():
    response = "{ \"key\": \"value\", \"number\": 42 }"
    assert force_cast(response, "json") == {"key": "value", "number": 42}
