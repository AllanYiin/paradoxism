import ast


def test_ast_parses_function():
    code = """
    def add(x, y):
        return x + y
    """
    tree = ast.parse(code)
    assert isinstance(tree.body[0], ast.FunctionDef)
