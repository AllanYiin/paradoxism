import time
import inspect
import ast
import textwrap
import traceback
import inspect
import linecache
from paradoxism.utils.utils import *
from paradoxism.base.agent import agent
from paradoxism.ops.base import prompt



@agent(model='gpt-4o-mini',system_prompt='你是一個擅長中文自然語言處理的超級幫手',temperature=0.2)
def chinese_seg(sentence: str) -> str:
    """
    請依照中文語意插入"|"以表示中文分詞
    """
    segmented_sentence = prompt('input:'+sentence+'\n\n'+'請依照中文語意插入"|"以表示中文分詞')  # 使用 prompt 函數
    return segmented_sentence


@agent(model='gpt-4o-mini',system_prompt='你是一個擅長中文情感偵測的超級幫手')
def emotion_detection(sentence: str) -> dict:
    """
    - 需要偵測的情感類型:
        正面情緒(positive_emotions)=[自信,快樂,體貼,幸福,信任,喜愛,尊榮,期待,感動,感謝,熱門,獨特,稱讚]
        負面情緒(negative_emotions)=[失望,危險,後悔,冷漠,懷疑,恐懼,悲傷,憤怒,擔心,無奈,煩悶,虛假,討厭,貶責,輕視]

    """
    results = prompt('input:'+sentence+'\n\n'+'當句子中有符合以上任何情感類型時，請盡可能的將符合的「情感類型」(key)及句子中的那些「觸及到情感類型的句子文字內容」(value)成對的列舉出來，一個句子可以觸及不只一種情感，請以dict形式輸出')
    return results


@agent(
    model='gpt-4o-mini',
    system_prompt='你是一個擅長中文實體識別的超級幫手'
)
def entity_detection(sentence: str) -> dict:
    """
    - 需要偵測的實體類型(entities)應該**包括但不僅限於**
      [中文人名,中文翻譯人名,外語人名,歌手/樂團/團體名稱,地名/地點,時間,公司機構名/品牌名,商品名,商品規格,化合物名/成分名,歌曲/書籍/作品名稱,其他專有名詞,金額,其他數值]
    - 你可以視情況擴充

    """
    results = prompt('input:'+sentence+'\n\n'+'句子中有偵測到符合上述實體類型時，也請盡可能的將符合的「實體類型」(key)及句子中的那些「觸及到實體類型句子文字內容｣(value)成對的列舉出來，一個句子可以觸及不只一種實體類型，請以dict形式輸出')
    return results


@agent(
    model='gpt-4o-mini',
    system_prompt='你是一個擅長中文意圖識別的超級幫手'
)
def intent_detection(sentence: str) -> dict:

    results = prompt('input:'+sentence+'\n\n'+'當你偵測到句子中有要求你代為執行某個任務(祈使句)、或是表達自己想要的事物或是行動、或是想查詢某資訊的意圖(intents)時，根據以意圖最普遍的**英文**講法之「名詞+動詞-ing」或動名詞的駝峰式命名形式來組成意圖類別(例如使用者說「請幫我訂今天下午5點去高雄的火車票」其意圖類別為TicketOrdering)，及句子中的那些「觸及到意圖類別的句子文字內容」成對的列舉出來，一個句子可以觸及不只一種意圖。請以dict形式輸出')
    return results


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
        all_outputs[sent]=output
    json_result = to_json(all_outputs)
    return json_result


import concurrent.futures

def process_sentence(sent):
    print(red_color(sent))
    print('------------')
    output = {'sentence': sent}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            'chinese_seg': executor.submit(chinese_seg, sent),
            'emotion_detection': executor.submit(emotion_detection, sent),
            'entity_detection': executor.submit(entity_detection, sent),
            'intent_detection': executor.submit(intent_detection, sent),
        }
        for key, future in futures.items():
            try:
                output[key] = future.result()
            except Exception as exc:
                print(f'{key} generated an exception: {exc}')
    return output


# def optimized_function(input_sentences, max_workers=4):
#     all_outputs = {}
#     input_sentences = input_sentences.split('\n')
#     with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
#         futures = {executor.submit(process_sentence,sent): i for i, sent in enumerate(input_sentences) if sent.strip()}
#         for future in concurrent.futures.as_completed(futures):
#             i = futures[future]
#             try:
#                 all_outputs[i] = future.result()
#             except Exception as exc:
#                 print(f'Sentence {i} generated an exception: {exc}')
#
#     json_result = to_json(all_outputs)
#     return json_result


import ast
import inspect
import textwrap
import concurrent.futures

import ast
import inspect
import textwrap
import concurrent.futures


class FlowOptimizer:
    def __init__(self):
        # 儲存優化後的源代碼
        self.optimized_source_code = ""

    def optimize_function(self, func):
        source = inspect.getsource(func)
        source = textwrap.dedent(source)
        tree = ast.parse(source)

        parallel_loops = self.detect_parallel_loops(tree)

        optimized_tree = self.rewrite_code(tree, parallel_loops)

        # 修正缺失的位置資訊
        ast.fix_missing_locations(optimized_tree)

        # 儲存優化後的源代碼
        self.optimized_source_code = ast.unparse(optimized_tree)

        # 編譯優化後的 AST
        optimized_code = compile(optimized_tree, filename="<ast>", mode="exec")

        # 建立命名空間並執行優化後的程式碼
        func_globals = func.__globals__.copy()
        exec(optimized_code, func_globals)
        optimized_func = func_globals[func.__name__]

        return optimized_func

    def detect_parallel_loops(self, tree):
        # 偵測可並行的迴圈
        # 簡化處理，假設頂層的 for 迴圈都可並行化
        parallel_loops = []
        func_def = tree.body[0]
        for node in func_def.body:
            if isinstance(node, ast.For):
                # 假設可以並行化
                parallel_loops.append(node)
        return parallel_loops

    def rewrite_code(self, tree, parallel_loops):
        func_def = tree.body[0]
        func_name = func_def.name
        func_args = func_def.args

        new_body = []

        # 複製 import 語句（如果有）
        imports = [node for node in func_def.body if isinstance(node, (ast.Import, ast.ImportFrom))]
        new_body.extend(imports)

        # 移除 import 語句後的函式主體
        func_body_without_imports = [node for node in func_def.body if not isinstance(node, (ast.Import, ast.ImportFrom))]

        # 處理函式主體
        for node in func_body_without_imports:
            if node in parallel_loops:
                # 重寫迴圈
                loop_node = node
                # 建立處理單個項目的函式
                loop_body = loop_node.body

                # 收集在迴圈體中使用的變數
                read_vars = set()
                write_vars = set()
                for stmt in loop_body:
                    for subnode in ast.walk(stmt):
                        if isinstance(subnode, ast.Name):
                            if isinstance(subnode.ctx, ast.Load):
                                read_vars.add(subnode.id)
                            elif isinstance(subnode.ctx, ast.Store):
                                write_vars.add(subnode.id)
                # 排除迴圈變數
                if isinstance(loop_node.target, ast.Name):
                    loop_var = loop_node.target.id
                    write_vars.add(loop_var)
                    if loop_var in read_vars:
                        read_vars.remove(loop_var)
                else:
                    raise NotImplementedError("僅支援簡單的迴圈變數。")

                # 處理函式的參數（讀取但未寫入的變數）
                func_args_vars = list(read_vars)
                # 返回的變數（寫入的變數，排除迴圈變數）
                return_vars = list(write_vars - set([loop_var]))

                # 建立處理函式的函式體
                # 替換迴圈體中的 'continue' 為 'return None'
                class ContinueToReturnNoneTransformer(ast.NodeTransformer):
                    def visit_Continue(self, node):
                        return ast.Return(value=ast.Constant(value=None))

                transformer = ContinueToReturnNoneTransformer()
                loop_body = [transformer.visit(stmt) for stmt in loop_body]

                process_func_name = f"_process_{loop_var}"
                process_func_args = ast.arguments(
                    posonlyargs=[],
                    args=[ast.arg(arg=loop_var)] + [ast.arg(arg=var) for var in func_args_vars],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[]
                )
                # 如果有返回變數，添加返回語句
                if return_vars:
                    return_stmt = ast.Return(value=ast.Dict(
                        keys=[ast.Constant(value=var) for var in return_vars],
                        values=[ast.Name(id=var, ctx=ast.Load()) for var in return_vars]
                    ))
                    process_func_body = loop_body + [return_stmt]
                else:
                    process_func_body = loop_body

                process_func_def = ast.FunctionDef(
                    name=process_func_name,
                    args=process_func_args,
                    body=process_func_body,
                    decorator_list=[],
                    lineno=loop_node.lineno,
                    col_offset=loop_node.col_offset
                )
                new_body.append(process_func_def)

                # 使用 ThreadPoolExecutor 重寫迴圈
                # 創建 executor
                executor_setup = ast.With(
                    items=[ast.withitem(
                        context_expr=ast.Call(
                            func=ast.Name(id='ThreadPoolExecutor', ctx=ast.Load()),
                            args=[],
                            keywords=[]
                        ),
                        optional_vars=ast.Name(id='executor', ctx=ast.Store())
                    )],
                    body=[],
                    lineno=loop_node.lineno,
                    col_offset=loop_node.col_offset
                )

                # 提交任務
                if isinstance(loop_node.target, ast.Name):
                    loop_var_name = loop_node.target.id
                    loop_var_load = ast.Name(id=loop_var_name, ctx=ast.Load())
                    loop_var_store = ast.Name(id=loop_var_name, ctx=ast.Store())
                else:
                    raise NotImplementedError("僅支援簡單的迴圈變數。")

                # 構建 futures 的列表解析式
                futures_assign = ast.Assign(
                    targets=[ast.Name(id='futures', ctx=ast.Store())],
                    value=ast.ListComp(
                        elt=ast.Call(
                            func=ast.Attribute(value=ast.Name(id='executor', ctx=ast.Load()), attr='submit', ctx=ast.Load()),
                            args=[ast.Name(id=process_func_name, ctx=ast.Load())] + [loop_var_load] + [ast.Name(id=var, ctx=ast.Load()) for var in func_args_vars],
                            keywords=[]
                        ),
                        generators=[ast.comprehension(
                            target=loop_var_store,
                            iter=loop_node.iter,
                            ifs=[],  # 'ast.For' 沒有 'ifs' 屬性，因此設為空列表
                            is_async=0
                        )],
                    ),
                    lineno=loop_node.lineno,
                    col_offset=loop_node.col_offset
                )

                executor_setup.body.append(futures_assign)

                # 初始化 'all_outputs'（如果尚未初始化）
                all_outputs_initialized = any(
                    isinstance(stmt, ast.Assign) and
                    any(isinstance(t, ast.Name) and t.id == 'all_outputs' for t in stmt.targets)
                    for stmt in new_body
                )
                if not all_outputs_initialized:
                    all_outputs_init = ast.Assign(
                        targets=[ast.Name(id='all_outputs', ctx=ast.Store())],
                        value=ast.List(elts=[], ctx=ast.Load())
                    )
                    new_body.append(all_outputs_init)

                # 收集結果，忽略 None 值
                result_loop_body = [
                    ast.Assign(
                        targets=[ast.Name(id='result', ctx=ast.Store())],
                        value=ast.Call(
                            func=ast.Attribute(value=ast.Name(id='future', ctx=ast.Load()), attr='result', ctx=ast.Load()),
                            args=[],
                            keywords=[]
                        )
                    ),
                    ast.If(
                        test=ast.Compare(
                            left=ast.Name(id='result', ctx=ast.Load()),
                            ops=[ast.IsNot()],
                            comparators=[ast.Constant(value=None)]
                        ),
                        body=[
                            ast.Expr(
                                value=ast.Call(
                                    func=ast.Attribute(value=ast.Name(id='all_outputs', ctx=ast.Load()), attr='append', ctx=ast.Load()),
                                    args=[ast.Name(id='result', ctx=ast.Load())],
                                    keywords=[]
                                )
                            )
                        ],
                        orelse=[]
                    )
                ]

                result_loop = ast.For(
                    target=ast.Name(id='future', ctx=ast.Store()),
                    iter=ast.Name(id='futures', ctx=ast.Load()),
                    body=result_loop_body,
                    orelse=[],
                    lineno=loop_node.lineno,
                    col_offset=loop_node.col_offset
                )

                executor_setup.body.append(result_loop)

                new_body.append(executor_setup)

            else:
                new_body.append(node)

        # 添加 ThreadPoolExecutor 的 import 語句
        import_stmt = ast.ImportFrom(
            module='concurrent.futures',
            names=[ast.alias(name='ThreadPoolExecutor', asname=None)],
            level=0
        )
        new_body.insert(0, import_stmt)

        # 建立新的函式定義
        new_func_def = ast.FunctionDef(
            name=func_name,
            args=func_args,
            body=new_body,
            decorator_list=[],
            lineno=func_def.lineno,
            col_offset=func_def.col_offset
        )

        # 建立模組
        optimized_tree = ast.Module(body=[new_func_def], type_ignores=[])

        return optimized_tree


# 測試函數
if __name__ == "__main__":
    test_sentences = """我想聽茄子蛋的手榴彈。
    大哥去二哥家，去找三哥说四哥被五哥騙去六哥家偷了七哥放在八哥房間裡的九哥借給十哥想要送给十一哥的1000元，請問誰是小偷
    我今天非常高興，因為我獲得了升職。
    請幫我訂明天下午3點去台北的火車票。"""
    # st=time.time()
    result = chinese_nlp(test_sentences.strip())
    # print(result,time.time()-st)

    #
    # st=time.time()
    # result2 = optimized_function(test_sentences.strip(), max_workers=4)
    # print(result2,time.time()-st)


    #
    # # Create an instance of FlowOptimizer
    # optimizer = FlowOptimizer()
    #
    # # Get the optimized function
    # optimized_chinese_nlp = optimizer.optimize_function(chinese_nlp)
    # print(optimizer.optimized_source_code)
    # # Now you can use the optimized function
    # result = optimized_chinese_nlp(test_sentences)
    # print(result)