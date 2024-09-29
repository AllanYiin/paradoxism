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
import networkx as nx
import concurrent.futures

import ast
import networkx as nx

import ast
import inspect
import textwrap
import concurrent.futures



class FlowGraphOptimizer:
    def __init__(self, source_code: str):
        """
        初始化，解析源碼並生成語法樹
        """
        self.source_code = source_code
        self.tree = ast.parse(source_code)
        self.dependency_graph = nx.DiGraph()
        self.loop_body = None
        self.loop_variable = None
        self.loop_iterable = None

    def analyze_dependencies(self):
        """
        分析語法樹中的變數相依性，構建相依性圖
        """
        assignments = {}
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Assign):
                # 取得被賦值的變數名
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        assignments[var_name] = node.lineno
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                # 追蹤使用變數的行
                for arg in node.value.args:
                    if isinstance(arg, ast.Name):
                        var_name = arg.id
                        if var_name in assignments:
                            self.dependency_graph.add_edge(assignments[var_name], node.lineno)

    def detect_loop_body(self):
        """
        檢測程式碼中的 for 迴圈，並識別出可併行處理的部分
        """
        for node in ast.walk(self.tree):
            if isinstance(node, ast.For):
                self.loop_body = node.body
                self.loop_variable = node.target.id  # 迴圈變數名稱
                self.loop_iterable = ast.unparse(node.iter)  # 迴圈可迭代對象
                break

    def generate_subfunctions(self):
        """
        將迴圈內的步驟提取成獨立的子函數，並檢測其可平行化的可能性
        """
        subfunctions = []
        if self.loop_body:
            for step in self.loop_body:
                if isinstance(step, ast.Assign):
                    func_name = f"subtask_{step.lineno}"
                    subfunctions.append(f"def {func_name}({self.loop_variable}):\n")
                    subfunctions.append(f"    return {ast.unparse(step.value)}\n")
        return subfunctions

    def generate_optimized_code(self):
        """
        根據可平行步驟，生成優化後的程式碼，針對迴圈內部進行平行化處理
        """
        optimized_code = []
        # 動態生成 import 語句
        optimized_code.append("import concurrent.futures\n")

        # 動態生成子函數
        subfunctions = self.generate_subfunctions()
        optimized_code.extend(subfunctions)

        # 動態生成主函數頭部
        optimized_code.append(f"\ndef optimized_function({self.loop_iterable}, max_workers=4):\n")
        optimized_code.append(f"    all_outputs = {{}}\n")

        # 迴圈處理邏輯
        if self.loop_body:
            optimized_code.append(  "with "+"concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:")
            optimized_code.append( f"    futures = {{executor.submit(subtask_{self.loop_body[0].lineno}, {self.loop_variable}.strip()): i for i, {self.loop_variable} in enumerate({self.loop_iterable}) if {self.loop_variable}.strip()}}\n")
            optimized_code.append("        for future in concurrent.futures.as_completed(futures):\n")
            optimized_code.append("            i = futures[future]\n")
            optimized_code.append("            try:\n")
            optimized_code.append("                all_outputs[i] = future.result()\n")
            optimized_code.append("            except Exception as exc:\n")
            optimized_code.append("                print(f'Exception: {exc}')\n")
        else:
            # 如果沒有迴圈，則直接回傳源碼（不平行化）
            for node in self.tree.body[0].body:
                optimized_code.append(f"    {ast.unparse(node)}\n")

        optimized_code.append("    return all_outputs\n")

        return "".join(optimized_code)

    def optimize(self):
        """
        綜合執行優化流程，並返回優化後的程式碼
        """
        self.analyze_dependencies()
        self.detect_loop_body()
        return self.generate_optimized_code()


# 測試部分
source_code = """
def process_sentence(sent: str) -> dict:
    output = {'sentence': sent}
    output['seg_sentence'] = chinese_seg(sent)
    output['emotion_detection'] = emotion_detection(sent)
    output['entity_detection'] = entity_detection(sent)
    output['intent_detection'] = intent_detection(sent)
    return output

def chinese_nlp(input_sentences: str) -> str:
    input_sentences = input_sentences.split('\\n')
    all_outputs = {}
    for i in range(len(input_sentences)):
        sent = input_sentences[i].strip()
        if not sent:
            continue
        output = process_sentence(sent)
        all_outputs[i] = output
    return all_outputs
"""


# # 使用 FlowGraphOptimizer 進行優化
# optimizer = FlowGraphOptimizer(code1)
# optimized_code = optimizer.optimize()
# print("優化後的程式碼:\n", optimized_code)

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