from paradoxism.ops.convert import force_cast
from datetime import datetime
# 測試字符串轉型
# response = "The result is: Hello World"
# assert force_cast(response, "str") == "Hello World", "Failed string test"

# 測試數字轉型（整數）
response = "Some numbers: 12345 is the result."
results=force_cast(response, "int")
assert results== 12345, "Failed integer test"

# 測試數字轉型（整數）
response = "Some numbers: 12,345 is the result."
assert force_cast(response, "int") == 12345, "Failed integer test"

# 測試數字轉型（浮點數）
response = "Value: 123.45 is the answer."
assert force_cast(response, "float") == 123.45, "Failed float test"

# 測試數字轉型（浮點數）
response = "Value: 4e-5 is the answer."
result=force_cast(response, "float")
assert  result== 0.00004, "Failed float test"

# 測試日期轉型
response = "Today's date is 2023-10-01"
result=force_cast(response, "date")
assert  result== datetime(2023, 10, 1), "Failed date test"

# 測試字典轉型
response = "Here is a JSON: {\"key\": \"value\"}"
result=force_cast(response, "dict")
assert result== {"key": "value"}, "Failed dict test"

# 測試列表轉型
response = "List: [1, 2, 3, 4]"
assert force_cast(response, "list") == [1, 2, 3, 4], "Failed list test"

# 測試 JSON 轉型
response = "Here is a JSON: {\"key\": \"value\"}"
assert force_cast(response, "json") == {"key": "value"}, "Failed JSON test"

# 測試 JSON schema 驗證
response = "{\"name\": \"John\", \"age\": 30}"
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"}
    },
    "required": ["name", "age"]
}
assert force_cast(response, "json_schema", schema) == {"name": "John", "age": 30}, "Failed JSON schema test"

# 測試 XML 轉型
response = "<person><name>John</name><age>30</age></person>"
xml_result = force_cast(response, "xml")
assert xml_result.tag == "person" and xml_result.find("name").text == "John", "Failed XML test"

# 測試 Markdown 轉型
response = "# Title\nSome text."
markdown_result = force_cast(response, "markdown")
assert "<h1>Title</h1>" in markdown_result, "Failed Markdown test"

# 測試 HTML 轉型
response = "&lt;div&gt;Some content&lt;/div&gt;"
assert force_cast(response, "html") == "<div>Some content</div>", "Failed HTML test"

response_code=open('../doc/docstring_style.md','r',encoding='utf-8').read()
result=force_cast(response_code, "code")
print(result)






# 測試邊界情況：無效的 JSON 格式
response = "Invalid JSON: {key: value}"
assert "Error" in force_cast(response, "json"), "Failed invalid JSON test"

# 測試空字符串輸入
response = ""
assert force_cast(response, "str") == "", "Failed empty string test"

# 測試不匹配的格式
response = "This is not a number: abc"
assert "Error" in force_cast(response, "int"), "Failed non-numeric int test"

# 測試無雜訊的 JSON
response = "{ \"key\": \"value\", \"number\": 42 }"
assert force_cast(response, "json") == {"key": "value", "number": 42}, "Failed clean JSON test"
