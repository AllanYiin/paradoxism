import ast
import networkx as nx
import matplotlib.pyplot as plt
from paradoxism.ops.ast import *
from paradoxism.utils.utils import PrintException
code='''
def collect_news():
    results={}
    stocks={"2301.TW":"光寶科","2308.TW":"台達電"}
    for k,v in  stocks.items():
        print(f'{v}({k})')
        results[k]=query_yahoo_news(k)
    return results
'''
code1 = '''
def chinese_nlp(input_sentences: str) -> str:
    input_sentences = input_sentences.split('\\n')
    all_outputs = {}
    for i in range(len(input_sentences)):
        sent = input_sentences[i].strip()
        if not sent:
            continue
        output = {'sentence': sent}
        print(f"Processing: {sent}")
        output['seg_sentence'] = chinese_seg(sent)
        output['emotion_detection'] = emotion_detection(sent)
        output['entity_detection'] = entity_detection(sent)
        output['intent_detection'] = intent_detection(sent)
        all_outputs[i]=output
    json_result = to_json(all_outputs)
    return json_result
'''
import ast
import inspect
import networkx as nx
import concurrent.futures
from types import FunctionType
from collections import defaultdict, deque
from typing import Any, Dict, List


class FlowOptimizer:
    def __init__(self, func, max_workers: int = 4):
        self.func = func
        self.func_code = inspect.getsource(func)
        self.max_workers = max_workers
        self.ast_tree = ast.parse(self.func_code)
        self.graph = nx.DiGraph()
        self.steps = []
        self.step_indices = defaultdict(
            lambda: defaultdict(deque))  # Nested defaultdict for better indexing by type and scope
        self.scope_stack = []  # Stack to track the current scope during traversal
        self.input_arguments = []  # List to store input arguments
        self.returns = []  # List to store return nodes
        self._analyze_ast()
        self._build_dependency_graph()

    def _analyze_ast(self):
        """
        Analyzes the AST tree to extract execution steps and input arguments.
        """

        def _analyze_node(node):
            # Skip nodes that are not relevant for optimization
            if not isinstance(node, (
            ast.FunctionDef, ast.ClassDef, ast.Assign, ast.Call, ast.For, ast.While, ast.BinOp, ast.Return)):
                return
            if isinstance(node, ast.FunctionDef):
                self.scope_stack.append(node.name)
                # Store function arguments
                self.input_arguments = [arg.arg for arg in node.args.args]
            elif isinstance(node, ast.ClassDef):
                self.scope_stack.append(node.name)

            node_scope = self._get_node_scope(node)
            if isinstance(node, (ast.Assign, ast.Call, ast.For, ast.While, ast.BinOp)):  # Also consider expressions
                self.steps.append(node)
                self.step_indices[type(node)][node_scope].append(
                    len(self.steps) - 1)  # Store indices by node type and scope for efficient lookup
            if isinstance(node, ast.Return):
                self.returns.append(node)
            if hasattr(node, 'body') and isinstance(node.body, list):
                for child in node.body:
                    _analyze_node(child)  # Recursively analyze child nodes
                    setattr(child, 'parent', node)
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                self.scope_stack.pop()

        for node in ast.iter_child_nodes(self.ast_tree):
            _analyze_node(node)

    def _get_node_scope(self, node: ast.AST) -> str:
        """
        Determines the scope of a given AST node to further refine dependency analysis.
        """
        # Uses stack to determine the current scope based on nested structures.
        if self.scope_stack:
            return '::'.join(self.scope_stack)
        return 'global'

    def _build_dependency_graph(self):
        """
        Builds a dependency graph based on the AST nodes.
        """
        for idx, step in enumerate(self.steps):
            self.graph.add_node(idx, step=step)
            dependencies = self._find_dependencies(step)
            node_scope = self._get_node_scope(step)
            dep_indices = self.step_indices[type(step)][node_scope]  # Cache dep_indices to avoid repeated lookups
            for dep in dependencies:
                dep_idx = None
                for i in range(len(dep_indices)):
                    potential_idx = dep_indices[i]
                    if self.steps[potential_idx] == dep:
                        dep_idx = potential_idx
                        dep_indices.remove(potential_idx)
                        break
                if dep_idx is not None:
                    self.graph.add_edge(dep_idx, idx)

    def _find_dependencies(self, node: ast.AST) -> List[ast.AST]:
        """
        Finds dependencies of a given AST node.
        """
        dependencies = []
        potential_dependencies = []
        node_scope = self._get_node_scope(node)
        # Limit the potential dependencies based on node type and scope.
        if isinstance(node, (ast.Assign, ast.BinOp, ast.Call)):
            potential_dependencies = [
                                         self.steps[idx] for idx in list(self.step_indices[ast.Assign][node_scope])
                                     ] + [
                                         self.steps[idx] for idx in list(self.step_indices[ast.Call][node_scope])
                                     ] + [
                                         self.steps[idx] for idx in list(self.step_indices[ast.BinOp][node_scope])
                                     ]

        for other in potential_dependencies:
            if self._is_dependent(node, other):
                dependencies.append(other)
        return dependencies

    def _is_dependent(self, node1: ast.AST, node2: ast.AST) -> bool:
        """
        Determines if node1 is dependent on node2.
        """
        # Check for assignment dependencies (variable usage).
        if isinstance(node1, ast.Assign) and isinstance(node2, ast.Assign):
            targets1 = [t.id for t in node1.targets if isinstance(t, ast.Name)]
            targets2 = [t.id for t in node2.targets if isinstance(t, ast.Name)]
            return any(target in targets2 for target in targets1)

        # Check for function call dependencies (arguments).
        if isinstance(node1, ast.Call):
            if isinstance(node2, ast.Assign):
                # Check if node2 assigns a variable that is used as an argument in node1.
                targets2 = [t.id for t in node2.targets if isinstance(t, ast.Name)]
                arguments = [arg.id for arg in node1.args if isinstance(arg, ast.Name)]
                return any(arg in targets2 for arg in arguments)
            elif isinstance(node2, ast.Call):
                # Check if the return value of node2 is used in node1.
                if isinstance(node2.func, ast.Attribute) and isinstance(node1.func, ast.Attribute):
                    # Handle attribute calls (e.g., obj.method)
                    return (node2.func.attr == node1.func.attr and
                            hasattr(node2.func.value, 'id') and hasattr(node1.func.value, 'id') and
                            node2.func.value.id == node1.func.value.id)
                elif isinstance(node2.func, ast.Name) and isinstance(node1.func, ast.Name):
                    # Handle simple function calls
                    return node2.func.id == node1.func.id

        # Check for variable usage in binary operations or expressions.
        if isinstance(node1, ast.BinOp):
            if isinstance(node2, ast.Assign):
                targets2 = [t.id for t in node2.targets if isinstance(t, ast.Name)]
                # Check if any of the variables in the binary operation depend on an assigned value.
                variables_in_binop = [n.id for n in ast.iter_child_nodes(node1) if isinstance(n, ast.Name)]
                return any(var in targets2 for var in variables_in_binop)

        return False

    def detect_loops(self) -> List[List[int]]:
        """
        Detects loops in the dependency graph.
        """
        loops = list(nx.simple_cycles(self.graph))
        return loops

    def find_parallel_steps(self) -> List[int]:
        """
        Finds steps that can be executed in parallel.
        """
        independent_steps = []
        for node in self.graph.nodes:
            predecessors = list(self.graph.predecessors(node))
            if len(predecessors) == 0:
                independent_steps.append(node)
        return independent_steps

    def optimize(self) -> str:
        """
        Optimizes the function by adjusting steps to run in parallel where possible.
        Returns the optimized function code as a string.
        """
        optimized_code_lines = []

        # Import necessary modules
        optimized_code_lines.append("import concurrent.futures")
        optimized_code_lines.append("")

        # Extract original function code dynamically
        func_name = self.func.__name__
        func_args = ", ".join(self.input_arguments)
        optimized_code_lines.append(f"def optimized_{func_name}(*args, **kwargs, max_workers=4):")
        optimized_code_lines.append("    outputs = {}")
        optimized_code_lines.append("")

        # Extracting parallelizable loops and dynamically create functions
        for step in self.steps:
            if isinstance(step, ast.For):
                # Identify the loop target and iterable
                loop_target = ast.unparse(step.target)
                loop_iter = ast.unparse(step.iter)

                # Create a function to handle the loop body
                loop_body_code = ["    def process_item(" + loop_target + "):"]
                for loop_step in step.body:
                    loop_body_code.append(f"        {ast.unparse(loop_step)}")
                loop_body_code.append("        return output")  # Ensure correct return value
                optimized_code_lines.extend(loop_body_code)
                optimized_code_lines.append("")

                # Replace the loop with parallel processing
                optimized_code_lines.append(
                    f"    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:")
                optimized_code_lines.append(
                    f"        futures = [executor.submit(process_item, item) for item in {loop_iter}]")
                optimized_code_lines.append("        for future in concurrent.futures.as_completed(futures):")
                optimized_code_lines.append("            try:")
                optimized_code_lines.append("                process_result = future.result()")
                optimized_code_lines.append("                if process_result is not None:")
                optimized_code_lines.append(
                    "                    outputs.setdefault('results', []).append(process_result)")
                optimized_code_lines.append("            except Exception as exc:")
                optimized_code_lines.append("                print(f'Generated an exception: {exc}')")
                optimized_code_lines.append("")
            else:
                # For non-loop steps, just add the code
                optimized_code_lines.append(f"    {ast.unparse(step)}")

        # Wrap up the function with a return statement if necessary
        if self.returns:
            for return_node in self.returns:
                return_code = "    " + ast.unparse(return_node)
                optimized_code_lines.append(return_code)

        # Correct misplaced code and ensure proper return formatting
        optimized_code_lines.append("    json_result = to_json(outputs)")
        optimized_code_lines.append("    return json_result")

        # Join the generated code lines into a single string
        optimized_code = "\n".join(optimized_code_lines)
        return optimized_code

    def _execute_step(self, step: ast.AST, context: Dict[str, Any]) -> None:
        """
        Execute a step within the given context.
        """
        step_code = ast.unparse(step)
        try:
            exec(step_code, context)
        except Exception as exc:
            raise RuntimeError(f"Error executing step: {exc}") from exc
# Usage Example
def chinese_nlp(input_sentences: str) -> str:
    input_sentences = input_sentences.split('\n')
    all_outputs = {}
    for sent in input_sentences:
        sent = sent.strip()
        if not sent:
            continue
        output = {'sentence': sent}
        print(f"Processing: {sent}")
        output['chinese_seg'] = chinese_seg(sent)
        output['emotion_detection'] = emotion_detection(sent)
        output['entity_detection'] = entity_detection(sent)
        output['intent_detection'] = intent_detection(sent)
        all_outputs[sent] = output
    json_result = to_json(all_outputs)
    return json_result


def chinese_seg(sent):
    return f"Segmentation of '{sent}'"


def emotion_detection(sent):
    return f"Emotion detected in '{sent}'"


def entity_detection(sent):
    return f"Entities detected in '{sent}'"


def intent_detection(sent):
    return f"Intent detected in '{sent}'"


def to_json(data):
    import json
    return json.dumps(data, indent=4)


flow_optimizer = FlowOptimizer(chinese_nlp, max_workers=4)
optimized_code = flow_optimizer.optimize()
print("優化代碼\n",optimized_code)

#
# # 使用修正後的 CodeFlowParser
# parser = CodeFlowParser()
# execution_plan, dependencies = parser.parse(code)
# print("Execution Plan:", execution_plan)
# print("Cycles Detected:", parser.detect_cycles(parser.build_dependency_graph()))
# print("Optimized Dependencies:", parser.get_optimized_dependencies())
#
# # 可視化初始依賴圖
# G = parser.build_dependency_graph()
# parser.visualize_graph(G, "Initial Dependency Graph")
#
# # 可視化優化後的依賴圖
# optimized_G = parser.optimize_dependencies()
# parser.visualize_graph(optimized_G, "Optimized Dependency Graph")
#
# # 生成優化後的代碼
# optimized_code = parser.generate_optimized_code(max_workers=5)
# print("\nOptimized Code:\n")
# print(optimized_code)