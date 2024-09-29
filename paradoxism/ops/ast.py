import ast
import astor
import networkx as nx
import matplotlib.pyplot as plt
from collections import deque
from itertools import combinations
import textwrap
__all__ = ['CodeFlowParser']


class CodeFlowParser(ast.NodeVisitor):
    def __init__(self):
        self.code = None
        self.step_counter = 0
        self.steps = []
        self.dependencies = []
        self.last_step = None
        self.loop_stack = []
        self.loop_bodies = {}
        self.function_name = None
        self.function_args = []
        self.variable_counter = 0  # 用於生成唯一的變量名稱
        self.prev_node_type = None  # 用於檢查相鄰節點類型

    def next_step_id(self):
        """產生下一個執行單位的 id"""
        step_id = f'step{self.step_counter:03}'
        self.step_counter += 1
        return step_id

    def add_dependency(self, from_step, to_step):
        """新增依賴關係"""
        self.dependencies.append({'from': from_step, 'to': to_step})

    def visit_FunctionDef(self, node):
        """訪問函數定義"""
        self.function_name = node.name
        self.function_args = [arg.arg for arg in node.args.args]
        for stmt in node.body:
            self.visit(stmt)

    def visit_For(self, node):
        step_id = self.next_step_id()
        iter_node = node.iter
        target_node = node.target

        # 判斷是否為枚舉式迴圈
        is_enum_loop = isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id in ['range', 'enumerate']

        can_parallel = is_enum_loop and self.is_independent_loop(node)

        self.steps.append({
            'id': step_id,
            'iter_node': iter_node,
            'target_node': target_node,
            'parallelizable': can_parallel,
            'loop': True,
            'is_enum': is_enum_loop,
            'node': node  # 保存原始節點以便後續使用
        })

        if self.last_step:
            self.add_dependency(self.last_step, step_id)
        self.loop_stack.append(step_id)
        self.last_step = step_id

        # 訪問迴圈內的步驟，並將它們存儲在 loop_bodies 中
        loop_body_steps = []
        for stmt in node.body:
            loop_body_step = self.visit(stmt)
            if loop_body_step:
                loop_body_steps.extend(loop_body_step)  # 更新為 extend
        self.loop_bodies[step_id] = loop_body_steps

        # 重置 prev_node_type
        self.prev_node_type = None

        return [step_id]

    def visit_While(self, node):
        # 類似處理，為簡化，這裡略過
        pass

    def visit_Assign(self, node):
        # 檢查前一個節點是否也是 Assign，如果是，則合併到同一個步驟
        if self.prev_node_type == 'Assign' and self.steps and not self.steps[-1]['loop']:
            self.steps[-1]['nodes'].append(node)
            step_id = self.steps[-1]['id']
        else:
            step_id = self.next_step_id()
            self.steps.append({
                'id': step_id,
                'nodes': [node],
                'parallelizable': False,
                'loop': False
            })
            if self.last_step:
                self.add_dependency(self.last_step, step_id)
            self.last_step = step_id
        self.prev_node_type = 'Assign'
        return [step_id]

    def visit_AugAssign(self, node):
        return self.visit_Assign(node)  # Treat AugAssign similarly to Assign

    def visit_Expr(self, node):
        # 檢查前一個節點是否也是 Expr，如果是，則合併到同一個步驟
        if self.prev_node_type == 'Expr' and self.steps and not self.steps[-1]['loop']:
            self.steps[-1]['nodes'].append(node)
            step_id = self.steps[-1]['id']
        else:
            step_id = self.next_step_id()
            self.steps.append({
                'id': step_id,
                'nodes': [node],
                'parallelizable': False,
                'loop': False
            })
            if self.last_step:
                self.add_dependency(self.last_step, step_id)
            self.last_step = step_id
        self.prev_node_type = 'Expr'
        return [step_id]

    def generic_visit(self, node):
        self.prev_node_type = type(node).__name__
        super().generic_visit(node)

    def get_node_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            return self.get_node_name(node.func)
        elif isinstance(node, ast.Attribute):
            return f"{self.get_node_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self.get_node_name(node.value)}[{self.get_node_name(node.slice)}]"
        elif isinstance(node, ast.Index):
            return self.get_node_name(node.value)
        return ast.dump(node)

    def is_independent_loop(self, node):
        """
        檢查迴圈內的步驟是否彼此獨立，沒有變數累加或依賴迭代間的數據
        """
        assigned_vars = set()
        for child in ast.walk(node):
            if isinstance(child, (ast.Assign, ast.AugAssign)):
                targets = child.targets if isinstance(child, ast.Assign) else [child.target]
                for target in targets:
                    var_name = self.get_node_name(target)
                    if var_name in assigned_vars:
                        return False  # 發現變數被多次賦值，可能有依賴
                    assigned_vars.add(var_name)
        return True

    def generate_execution_plan(self):
        plan = []
        for step in self.steps:
            plan.append({
                'id': step['id'],
                'iter': ast.unparse(step['iter_node']) if 'iter_node' in step else None,
                'target': ast.unparse(step['target_node']) if 'target_node' in step else None,
                'condition': step.get('condition'),
                'parallelizable': step['parallelizable'],
                'loop': step.get('loop', False),
                'is_enum': step.get('is_enum', False)
            })
        return plan

    def parse(self, code):
        self.code = code
        tree = ast.parse(code)
        self.visit(tree)
        return self.generate_execution_plan(), self.dependencies

    def build_dependency_graph(self):
        """建立初始的依賴圖"""
        G = nx.DiGraph()
        for step in self.steps:
            G.add_node(step['id'], **step)
        for dep in self.dependencies:
            G.add_edge(dep['from'], dep['to'])
        return G

    def detect_cycles(self, G):
        """檢測圖中的循環"""
        try:
            cycles = list(nx.find_cycle(G, orientation='original'))
            return cycles
        except nx.NetworkXNoCycle:
            return []

    def optimize_dependencies(self):
        """優化依賴關係，將可並行的步驟並行化"""
        original_G = self.build_dependency_graph()
        optimized_G = nx.DiGraph()

        # 追蹤節點的映射關係
        node_mapping = {}  # 原始節點ID到優化後節點ID的映射

        # 先添加所有節點到優化圖中，但不添加邊
        for node_id, node_data in original_G.nodes(data=True):
            optimized_G.add_node(node_id, **node_data)
            node_mapping[node_id] = node_id  # 初始映射為自身

        optimized_dependencies = []
        finished_steps = []

        for step in self.steps:
            step_id = step['id']
            if step_id in finished_steps:
                continue
            if step.get('loop', False) and step.get('is_enum', False) and step.get('parallelizable', False):
                # 可並行化的迴圈
                loop_body_steps =self.loop_bodies.get(step_id, [])

                # 移除迴圈內部的依賴關係
                for i in range(len(loop_body_steps) - 1):
                    if original_G.has_edge(loop_body_steps[i], loop_body_steps[i + 1]):
                        original_G.remove_edge(loop_body_steps[i], loop_body_steps[i + 1])



                # 添加迴圈節點到優化圖（已經添加）

                # 添加虛擬節點
                virtual_node = f'virtual_{step_id}'
                optimized_G.add_node(virtual_node, virtual=True)
                node_mapping[virtual_node] = virtual_node

                # 前置節點 -> 迴圈節點
                predecessors = list(original_G.predecessors(step_id))
                for pred in predecessors:
                    mapped_pred = node_mapping.get(pred, pred)
                    if {'from': mapped_pred, 'to': step_id} not in optimized_dependencies:
                        optimized_dependencies.append({'from': mapped_pred, 'to': step_id})

                # 迴圈節點 -> 迴圈體步驟（並行啟動）
                for body_step_id in loop_body_steps:
                    if {'from': step_id, 'to': body_step_id} not in optimized_dependencies:
                        optimized_dependencies.append({'from': step_id, 'to': body_step_id})

                # 迴圈體步驟 -> 虛擬節點
                for body_step_id in loop_body_steps:
                    if {'from': body_step_id, 'to': virtual_node} not in optimized_dependencies:
                        optimized_dependencies.append({'from': body_step_id, 'to': virtual_node})

                # # 虛擬節點 -> 後繼節點
                # successors = list(original_G.successors(step_id))
                # for succ in successors:
                #     mapped_succ = node_mapping.get(succ, succ)
                #     optimized_dependencies.append({'from': virtual_node, 'to': mapped_succ})
                finished_steps.append(step_id)
                finished_steps.extend(loop_body_steps)
                last_successors = list(original_G.successors(loop_body_steps[-1]))
                for last_successors_step_id in last_successors:
                    if {'from': virtual_node, 'to': last_successors_step_id} not in optimized_dependencies:
                        optimized_dependencies.append({'from': virtual_node, 'to': last_successors_step_id})
                        finished_steps.append(last_successors_step_id)

                # 更新映射關係
                node_mapping[step_id] = step_id
                for body_step_id in loop_body_steps:
                    node_mapping[body_step_id] = body_step_id

            else:
                # 非並行化的步驟
                # 檢查前驅和後繼節點是否在優化後的圖中
                predecessors = list(original_G.predecessors(step_id))
                #successors = list(original_G.successors(step_id))

                for pred in predecessors:
                    mapped_pred = node_mapping.get(pred)
                    if mapped_pred and optimized_G.has_node(mapped_pred):
                        optimized_dependencies.append({'from': mapped_pred, 'to': step_id})
                finished_steps.append(step_id)
                #
                # for succ in successors:
                #     mapped_succ = node_mapping.get(succ)
                #     if mapped_succ and optimized_G.has_node(mapped_succ):
                #         optimized_dependencies.append({'from': step_id, 'to': mapped_succ})

        # 在 optimized_G 中添加優化後的依賴關係
        optimized_G.add_edges_from([(dep['from'], dep['to']) for dep in optimized_dependencies])

        # 檢測並移除循環
        cycles = self.detect_cycles(optimized_G)
        while cycles:
            print("Optimized graph has cycles:", cycles)
            for edge in cycles:
                if optimized_G.has_edge(edge[0], edge[1]):
                    optimized_G.remove_edge(edge[0], edge[1])
                    print(f"Removed edge: {edge[0]} -> {edge[1]}")
            cycles = self.detect_cycles(optimized_G)
            print("Cycles removed in optimized graph.")

        return optimized_G

    def get_optimized_dependencies(self):
        optimized_G = self.optimize_dependencies()
        # 將優化後的依賴關係轉換為列表
        optimized_dependencies = []
        for edge in optimized_G.edges():
            optimized_dependencies.append({'from': edge[0], 'to': edge[1]})
        return optimized_dependencies

    def visualize_graph(self, G, title="Dependency Graph"):
        import matplotlib.pyplot as plt
        pos = nx.spiral_layout(G)
        labels = {node: node for node in G.nodes()}
        node_colors = []
        for node in G.nodes(data=True):
            if node[0].startswith("virtual_"):
                node_colors.append('red')  # 虛擬節點顯示為紅色
            elif node[1].get('parallelizable', False):
                node_colors.append('lightgreen')
            elif node[1].get('loop', False):
                node_colors.append('orange')
            else:
                node_colors.append('lightblue')
        nx.draw(G, pos, with_labels=True, labels=labels, node_color=node_colors, edge_color='gray', node_size=2000, font_size=10)
        plt.title(title)
        plt.show()

    def generate_optimized_code(self, max_workers=5):
        """
        基於優化後的依賴圖生成優化的 Python 代碼，使用 ThreadPoolExecutor 進行並行執行
        """
        optimized_G = self.optimize_dependencies()

        # 確保優化後的依賴圖是無循環的
        cycles = self.detect_cycles(optimized_G)
        if cycles:
            raise ValueError(f"Optimized dependency graph contains cycles: {cycles}")

        # 構建步驟順序
        ordered_steps = list(nx.topological_sort(optimized_G))

        # 使用 AST 模塊動態構建代碼
        module = ast.Module(body=[], type_ignores=[])

        # 添加必要的導入語句
        import_futures = ast.ImportFrom(
            module='concurrent.futures',
            names=[
                ast.alias(name='ThreadPoolExecutor', asname=None),
                ast.alias(name='as_completed', asname=None)
            ],
            level=0
        )
        module.body.extend([import_futures, ast.Expr(value=ast.Constant(value=''))])  # 添加空行

        # 定義優化後的函數
        func_def = ast.FunctionDef(
            name=self.function_name if self.function_name else 'optimized_function',
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg=arg_name) for arg_name in self.function_args],
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[]
            ),
            body=[],
            decorator_list=[]
        )
        module.body.append(func_def)

        # 初始化必要的變量
        func_def.body.append(ast.Assign(
            targets=[ast.Name(id='all_outputs', ctx=ast.Store())],
            value=ast.List(elts=[], ctx=ast.Load())
        ))

        # 定義存儲處理函數的列表
        processing_functions = {}

        # 處理步驟
        for step_id in ordered_steps:
            node_data = optimized_G.nodes[step_id]
            if node_data.get('loop', False):
                if node_data.get('is_enum', False) and node_data.get('parallelizable', False):
                    # 並行化的枚舉式迴圈
                    loop_id = step_id
                    iter_node = node_data['iter_node']
                    target_node = node_data['target_node']

                    # 定義處理函數
                    process_func_name = f"process_{loop_id}"
                    if process_func_name not in processing_functions:
                        process_func_def = self.create_processing_function(loop_id, processing_functions)
                        module.body.append(process_func_def)

                    # 添加 ThreadPoolExecutor with 語句
                    with_stmt = ast.With(
                        items=[ast.withitem(
                            context_expr=ast.Call(
                                func=ast.Name(id='ThreadPoolExecutor', ctx=ast.Load()),
                                args=[],
                                keywords=[ast.keyword(arg='max_workers', value=ast.Constant(value=max_workers))]
                            ),
                            optional_vars=ast.Name(id='executor', ctx=ast.Store())
                        )],
                        body=[]
                    )
                    func_def.body.append(with_stmt)

                    # futures = []
                    with_stmt.body.append(ast.Assign(
                        targets=[ast.Name(id='futures', ctx=ast.Store())],
                        value=ast.List(elts=[], ctx=ast.Load())
                    ))

                    # 在 with 區塊內添加 for 循環
                    for_loop = ast.For(
                        target=target_node,
                        iter=iter_node,
                        body=[],
                        orelse=[]
                    )
                    with_stmt.body.append(for_loop)

                    # futures.append(executor.submit(process_func, *args))
                    submit_call = ast.Expr(value=ast.Call(
                        func=ast.Attribute(value=ast.Name(id='futures', ctx=ast.Load()), attr='append', ctx=ast.Load()),
                        args=[
                            ast.Call(
                                func=ast.Attribute(value=ast.Name(id='executor', ctx=ast.Load()), attr='submit', ctx=ast.Load()),
                                args=[
                                    ast.Name(id=process_func_name, ctx=ast.Load()),
                                    *self.get_loop_variables(target_node)
                                ],
                                keywords=[]
                            )
                        ],
                        keywords=[]
                    ))
                    for_loop.body.append(submit_call)

                    # 虛擬節點處理：等待所有 futures 完成
                    for_future = ast.For(
                        target=ast.Name(id='future', ctx=ast.Store()),
                        iter=ast.Call(
                            func=ast.Name(id='as_completed', ctx=ast.Load()),
                            args=[ast.Name(id='futures', ctx=ast.Load())],
                            keywords=[]
                        ),
                        body=[],
                        orelse=[]
                    )
                    func_def.body.append(for_future)

                    # result = future.result()
                    assign_result = ast.Assign(
                        targets=[ast.Name(id='result', ctx=ast.Store())],
                        value=ast.Call(
                            func=ast.Attribute(value=ast.Name(id='future', ctx=ast.Load()), attr='result', ctx=ast.Load()),
                            args=[],
                            keywords=[]
                        )
                    )
                    for_future.body.append(assign_result)

                    # all_outputs.append(result)
                    append_result = ast.Expr(
                        value=ast.Call(
                            func=ast.Attribute(value=ast.Name(id='all_outputs', ctx=ast.Load()), attr='append', ctx=ast.Load()),
                            args=[ast.Name(id='result', ctx=ast.Load())],
                            keywords=[]
                        )
                    )
                    for_future.body.append(append_result)
                else:
                    # 非並行化的迴圈，直接添加
                    func_def.body.append(node_data['node'])
            elif node_data.get('virtual', False):
                # 虛擬節點，不需要在代碼中表示
                continue
            else:
                # 非迴圈步驟，將所有節點添加到函數體中
                for node in node_data.get('nodes', []):
                    func_def.body.append(node)

        # 返回結果
        return_stmt = ast.Return(value=ast.Name(id='all_outputs', ctx=ast.Load()))
        func_def.body.append(return_stmt)

        # 使用 astor 將 AST 轉換為代碼字符串
        optimized_code = astor.to_source(module)
        return optimized_code

    def create_processing_function(self, loop_id, processing_functions):
        """
        動態創建處理函數，用於並行執行的迴圈體
        """
        process_func_name = f"process_{loop_id}"

        # 獲取迴圈步驟的數據
        loop_step = next((s for s in self.steps if s['id'] == loop_id), None)
        if loop_step:
            target_node = loop_step['target_node']
            # 創建函數參數
            param_names = self.get_loop_variable_names(target_node)
            func_args = [ast.arg(arg=param_name) for param_name in param_names]

            # 定義處理函數
            process_func_def = ast.FunctionDef(
                name=process_func_name,
                args=ast.arguments(
                    posonlyargs=[],
                    args=func_args,
                    vararg=None,
                    kwonlyargs=[],
                    kw_defaults=[],
                    kwarg=None,
                    defaults=[]
                ),
                body=[],
                decorator_list=[]
            )

            # 從 loop_bodies 中提取迴圈體的步驟，並將其添加到處理函數中
            loop_body_steps = self.loop_bodies.get(loop_id, [])
            for body_step_id in loop_body_steps:
                body_step = next((s for s in self.steps if s['id'] == body_step_id), None)
                if body_step:
                    for body_node in body_step.get('nodes', []):
                        process_func_def.body.append(body_node)

            # 收集賦值的變量
            assigned_vars = set()
            for node in process_func_def.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            assigned_vars.add(target.id)

            # 決定返回值
            if assigned_vars:
                return_values = [ast.Name(id=var, ctx=ast.Load()) for var in assigned_vars]
                if len(return_values) == 1:
                    return_value = return_values[0]
                else:
                    return_value = ast.Tuple(elts=return_values, ctx=ast.Load())
                process_func_def.body.append(ast.Return(value=return_value))
            else:
                # 如果沒有賦值，返回 None
                process_func_def.body.append(ast.Return(value=ast.Constant(value=None)))

            processing_functions[process_func_name] = process_func_def
            return process_func_def

    def get_loop_variable_names(self, target_node):
        """獲取迴圈目標變量的名稱列表"""
        param_names = []
        if isinstance(target_node, ast.Name):
            param_names.append(target_node.id)
        elif isinstance(target_node, ast.Tuple):
            for elt in target_node.elts:
                if isinstance(elt, ast.Name):
                    param_names.append(elt.id)
                else:
                    # 處理其他情況
                    param_names.append(ast.unparse(elt))
        else:
            # 處理其他情況
            param_names.append(ast.unparse(target_node))
        return param_names

    def get_loop_variables(self, target_node):
        """獲取迴圈目標變量的 AST 節點列表"""
        if isinstance(target_node, ast.Name):
            return [ast.Name(id=target_node.id, ctx=ast.Load())]
        elif isinstance(target_node, ast.Tuple):
            return [ast.Name(id=elt.id, ctx=ast.Load()) if isinstance(elt, ast.Name) else elt for elt in target_node.elts]
        else:
            return [target_node]

    def has_dependencies(self, step_id):
        """檢查某個步驟是否有任何前置依賴"""
        return any(dep['to'] == step_id for dep in self.dependencies)

    def extract_iterable_from_loop(self, loop_id):
        """從迴圈步驟中提取可迭代對象"""
        loop_step = next((s for s in self.steps if s['id'] == loop_id), None)
        if loop_step:
            if 'iter_node' in loop_step:
                return ast.unparse(loop_step['iter_node'])
            elif 'condition' in loop_step:
                return loop_step['condition']
        return "iterable"

#
# def generate_mermaid_from_flow(flow_result):
#     mermaid_code = "graph TD\n"
#
#     # 設定每個步驟的節點
#     for step in flow_result['steps']:
#         code_snippet = step['code'].strip().replace('"', '\\"')  # 防止引號引發錯誤
#         # 截斷代碼片段，如果超過 50 個字元
#         if len(code_snippet) > 50:
#             code_snippet = code_snippet[:47] + "..."
#         mermaid_code += f'    {step["id"]}["{code_snippet}"]\n'
#
#     # 設定依賴關係
#     for dep in flow_result['dependencies']:
#         if dep["from"] == "step013" and dep["to"] == "step003":
#             # 跳過不合理的依賴關係
#             continue
#         mermaid_code += f'    {dep["from"]} --> {dep["to"]}\n'
#
#     # 處理 for 迴圈結構：將迴圈結束步驟回連到開頭
#     for step in flow_result['steps']:
#         if "for" in step["code"]:
#             loop_start = step["id"]
#             loop_end = None
#             # 找到迴圈內最後一個步驟
#             for dep in flow_result['dependencies']:
#                 if dep["from"] != loop_start and dep["to"] == loop_start:
#                     loop_end = dep["from"]
#             if loop_end:
#                 mermaid_code += f'    {loop_end} --> {loop_start} %% 迴圈返回\n'
#
#     return mermaid_code
#
# def generate_dependency_list_from_flow(flow_result):
#     # 初始化步驟ID依賴關係和步驟細節
#     dependencies_list = []
#     step_details = []
#
#     # 建立步驟細節
#     for step in flow_result['steps']:
#         step_info = {
#             "id": step["id"],
#             "code_range": step["code"],  # 代碼範圍
#             "external_calls": step.get("external_calls", [])  # 引用外部函數
#         }
#         step_details.append(step_info)
#
#     # 建立步驟之間的依賴關係列表
#     for dep in flow_result['dependencies']:
#         dependencies_list.append({
#             "from": dep["from"],
#             "to": dep["to"]
#         })
#
#     return dependencies_list, step_details
#
#
# def generate_networks_plot_from_flow(flow_result):
#     # 建立有向圖
#     G = nx.DiGraph()
#     # 建立步驟之間的依賴關係列表
#     for dep in flow_result['dependencies']:
#         G.add_edge(dep['from'], dep['to'])
#     # layouts=[
#     # nx.layout.circular_layout,
#     # nx.layout.kamada_kawai_layout,
#     # nx.layout.random_layout,
#     # nx.layout.rescale_layout,
#     # nx.layout.rescale_layout_dict,
#     # nx.layout.shell_layout,
#     # nx.layout.spring_layout,
#     # nx.layout.spectral_layout,
#     # nx.layout.planar_layout,
#     # nx.layout.fruchterman_reingold_layout,
#     # nx.layout.spiral_layout,
#     # nx.layout.multipartite_layout,
#     # nx.layout.arf_layout]
#
#     # for lay in layouts:
#     try:
#         plt.figure(figsize=(10, 6))
#         pos = nx.layout.spectral_layout(G)  # 使用 spring 布局來安排節點位置
#         nx.draw(G, pos, with_labels=True, node_size=3000, node_color="skyblue", font_size=10, font_weight="bold",
#                 arrows=True)
#
#         # 顯示圖形
#         plt.axis('off')
#         plt.title(f"Dependency Graph('spectral_layout')")
#         plt.savefig(f"dependency_graph_spectral_layout.png")
#         plt.show()
#         plt.close()
#     except Exception as e:
#         print(e)
#
#
# def topological_sort_with_levels(flow_result):
#     """
#     進行拓撲排序並將步驟分層，返回每一層的步驟（可以併行的部分）
#     """
#     # 建立有向圖
#     G = nx.DiGraph()
#     # 建立步驟之間的依賴關係列表
#     for dep in flow_result['dependencies']:
#         G.add_edge(dep['from'], dep['to'])
#
#     # 檢查是否有循環依賴
#     if not nx.is_directed_acyclic_graph(G):
#         raise ValueError("依賴關係圖包含循環依賴，無法進行拓撲排序")
#
#     # 進行拓撲排序並確定每個節點的層級
#     in_degree = {node: 0 for node in G.nodes}
#     for u, v in G.edges:
#         in_degree[v] += 1
#
#     # 使用 deque 進行拓撲排序
#     queue = deque([node for node in G.nodes if in_degree[node] == 0])
#     topological_layers = []
#     current_layer = []
#
#     while queue:
#         next_queue = deque()
#         while queue:
#             node = queue.popleft()
#             current_layer.append(node)
#
#             for neighbor in G.neighbors(node):
#                 in_degree[neighbor] -= 1
#                 if in_degree[neighbor] == 0:
#                     next_queue.append(neighbor)
#
#         topological_layers.append(current_layer)
#         current_layer = []
#         queue = next_queue
#
#     return topological_layers
#
#
# def handle_cycles(G):
#     # 檢查圖中是否有循環並處理遞迴或重複執行
#     try:
#         cycle = nx.find_cycle(G, orientation="original")
#         print("Cycle detected:", cycle)
#         return cycle
#     except nx.NetworkXNoCycle:
#         print("No cycle detected.")
#         return None
#



