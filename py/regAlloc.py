#--------------------------------------------------
#
# regAlloc.py
# liveness情報を用いた楽観的彩色によるレジスタ割り当て
#
# 実装の方針：
# 以下の状態遷移図に従ってレジスタ割り当てを行う
#
#  build →→→ simplify →→→ spill →→→ select
#    ↑           ↑          ↓         ↓
#    ↑           ←←←←←←←←←←←←         ↓
#    ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
#
# build: livenessの情報から、「変数x,yが同じ命令内で生きている」 iff 「x,yの間に枝がある」となるような、変数全体を頂点に持つグラフを形成する
# simplify: limit（引数として与えられるレジスタの最大数）未満の隣接頂点を持つ頂点をスタックに移動していく
# spill: simplifyでスタックに移動できなかった変数の中から候補を選択する
# select: スタックから頂点をとりながら、順にレジスタを割り当てていく。色付け不能なものがあれば、spillで候補として用意していた変数をメモリに割り当てする命令を挿入し、buildからやり直し
#
#--------------------------------------------------

import virtual
import liveness
from typing import List, Dict, Set, Tuple, Union
import itertools
import copy
import reglist
import error

# liveness情報からグラフを作成する
# グラフは 変数の名前 : {edgeを共有する変数の名前}
# という要素を持つ辞書
def build (lis:List[virtual.Virtual_Asm]) -> Tuple[Dict[str, Set]]:
    graph_int, graph_float = {}, {}

    # 生存解析
    live_int, live_float, def_int, use_int, def_float, use_float = liveness.AnalyzeLiveness(lis)

    # グラフ生成
    for live_set in live_int.values(): # intのグラフ生成
        for name in live_set:
            if name not in graph_int:
                graph_int[name] = set()
        if len(live_set) >= 2:
            for edge in itertools.combinations(live_set, 2):
                graph_int[edge[0]].add(edge[1])
                graph_int[edge[1]].add(edge[0])
    for live_set in live_float.values(): # floatのグラフ生成
        for name in live_set:
            if name not in graph_float:
                graph_float[name] = set()
        if len(live_set) >= 2:
            for edge in itertools.combinations(live_set, 2):
                graph_float[edge[0]].add(edge[1])
                graph_float[edge[1]].add(edge[0])

    return graph_int, graph_float, def_int, use_int, def_float, use_float

# limit未満の隣接ノードを持つノードを削除してスタックに移動する
def simplify (graph:Dict[str, Set], limit:int, stk:List[str]) -> Tuple[Dict[str, Set], List[str]]:
    while True: # 変化がでなくなるまでループする
        names = list(graph.keys())
        change_flag = False # 変化があったかを判定するフラグ
        for name in names:
            if len(graph[name]) < limit:
                stk.append(name)
                graph.pop(name) # グラフからノードを削除
                for key in graph: # 削除したノードを一端にもつ枝を削除
                    if name in graph[key]:
                        graph[key].remove(name)
                change_flag = True
        if change_flag:
            continue
        else: # グラフ内のどの変数をみても隣接ノード数がlimit以上になったのでループから抜ける
            break
    return graph, stk

# メモリ上に保持する（spillする）可能性のある変数を選ぶ
# 返り値は 与えられたgraphそのまま、spillする可能性のある変数の名前、spillする可能性のある変数を加えたスタック
def spill (graph:Dict[str, Set], stk:List[str], already_spilled:List[str]) -> Tuple[Dict[str, Set], str, List[str]]:
    if graph == {}:
        return graph, None, stk
    names = list(graph.keys())
    for name in names: # 適当に一番最初を選択（todo: 最適化）
        if name not in already_spilled: # すでにspillしたことのある変数は無限ループに陥る可能性があるのでダメ
            break
    stk.append(name)
    graph.pop(name) # グラフからノードを削除
    for key in graph: # 削除したノードを一端にもつ枝を削除
        if name in graph[key]:
            graph[key].remove(name)
    return graph, name, stk

# スタックからノードをポップしながら割り当てしていく
# 成功したらallocation(dict)を，失敗したらnode(str, メモリ上に保持する変数の候補)を返す
def select (graph:Dict[str, Set], stk:List[str], potential_spill:List[str], regs_list:List[str]) -> Union[Dict[str, Set], str]:
    # 最終的に返す割り当て結果
    allocation = {}
    while stk:
        alloc_success_flag = False # 割り当てが成功したかどうかを表すフラグ
        node = stk.pop()
        # 隣接ノードへ割り当てられているレジスタの集合を計算
        pair_nodes = graph[node] # nodeの隣接ノードの集合
        regs_allocated_to_pair_nodes = set()
        for pair_node in pair_nodes:
            if pair_node in allocation:
                regs_allocated_to_pair_nodes.add(allocation[pair_node])
        # 隣接ノードへ割り当てられているレジスタを使わないように割り当て
        for reg in regs_list:
            if reg not in regs_allocated_to_pair_nodes:
                allocation[node] = reg
                alloc_success_flag = True
                break
        if not alloc_success_flag:
            # ここにたどり着いていたら割り当て失敗
            if node in potential_spill:
                return node
            else:
                error.error("Register allocation failed.")
    return allocation

# 即値レジスタかどうかを判別
def isImmediate (name:str):
    for letter in name:
        if letter.isalpha():
            return False
    return True

# defされているがuseされていない命令は不要なので、のちに削除できるように変数名をunnecessaryにしておく
def removeUnnecessaryInstr (lis:List[virtual.Virtual_Asm], allocation_or_node_int, allocation_or_node_float):
    _, _, def_int, use_int, def_float, use_float = build(lis)
    # use_int, use_floatの中に入っている変数の集合
    use_int_set = set()
    use_float_set = set()
    for key in use_int:
        use_int_set |= use_int[key]
    for key in use_float:
        use_float_set |= use_float[key]

    # defのなかのitemがuseに入っていなければ、unnecessaryになる
    for key in def_int:
        if len(def_int[key]) > 0:
            def_item = list(def_int[key])[0]
            if def_item not in use_int_set:
                allocation_or_node_int[def_item] = "unnecessary"
    for key in def_float:
        if len(def_float[key]) > 0:
            def_item = list(def_float[key])[0]
            if def_item not in use_float_set:
                allocation_or_node_float[def_item] = "unnecessary"
    
    return allocation_or_node_int, allocation_or_node_float
    
# regAllocの前処理として，関数の「* args」のうち，使われていないargを「* not used args」として加え，use_int, use_floatに無理やり含まれるようにする
# （そうでないと前の関数のunnecessaryの対象になってしまう）
def findNotUsedArgs (lis:List[virtual.Virtual_Asm]) -> List[virtual.Virtual_Asm]:
    if lis[1].instr_name != "* args": # 引数がないのでスルー
        return lis
    
    # use_int, use_floatの中に入っている変数の集合を作る
    _, _, _, use_int, _, use_float = build(lis)
    use_int_set = set()
    use_float_set = set()
    for key in use_int:
        use_int_set |= use_int[key]
    for key in use_float:
        use_float_set |= use_float[key]

    # argsのリストを作る
    args_list = []
    for asm in lis:
        if asm.instr_name == "* args":
            args_list.append(asm.arg_list[0])
    # 使われていないargsのリストを作る
    not_used_args_list = []
    for arg in args_list:
        if arg.name not in use_int_set and arg.name not in use_float_set:
            not_used_args_list.append(arg)
    # 使われていないargsを「* not used args」として加える
    idx = 1
    while True:
        if lis[idx].instr_name == "* args":
            idx += 1
        else:
            break
    return lis[:idx] + [
        virtual.Virtual_Asm("* not used args", 1, [reg]) for reg in not_used_args_list
    ] + lis[idx:]

# 与えられた変数をメモリに割り当てるロード，ストア命令をlisの中に埋め込む
def memoryAlloc (
    lis:List[virtual.Virtual_Asm],
    node_int:str = None,
    def_int = None,
    use_int = None,
    node_float:str = None,
    def_float = None,
    use_float = None,
    ) -> List[virtual.Virtual_Asm]:
    # int
    store_pos_int = []
    restore_pos_int = []
    if node_int is not None:
        # storeを挿入する位置を計算。挿入する位置はnode_intが定義されている部分の直後
        for def_int_key in def_int:
            def_int_item = def_int[def_int_key]
            if node_int in def_int_item:
                store_pos_int.append(def_int_key + 1)
        # restoreを挿入する位置を計算。挿入する位置はnode_intが使用されている部分の直前
        for use_int_key in use_int:
            use_int_item = use_int[use_int_key]
            if node_int in use_int_item:
                restore_pos_int.append(use_int_key)
    # float
    store_pos_float = []
    restore_pos_float = []
    if node_float is not None:
        # storeを挿入する位置を計算
        if def_float is not None:
            for def_float_key in def_float:
                def_float_item = def_float[def_float_key]
                if node_float in def_float_item:
                    store_pos_float.append(def_float_key + 1)
        # restoreを挿入する位置を計算
        if use_float is not None:
            for use_float_key in use_float:
                use_float_item = use_float[use_float_key]
                if node_float in use_float_item:
                    restore_pos_float.append(use_float_key)
    # store,restoreをlisに入れていく
    new_lis = []
    store_pos_int_idx = 0
    restore_pos_int_idx = 0
    store_pos_float_idx = 0
    restore_pos_float_idx = 0
    store_pos_int_length = len(store_pos_int)
    restore_pos_int_length = len(restore_pos_int)
    store_pos_float_length = len(store_pos_float)
    restore_pos_float_length = len(restore_pos_float)
    for i in range(len(lis)):
        if store_pos_int_idx < store_pos_int_length and store_pos_int[store_pos_int_idx] == i:
            new_lis.append(virtual.Virtual_Asm("store", 2, [virtual.Reg(node_int, "int"), virtual.Reg(node_int, 'label')]))
            store_pos_int_idx += 1
        if restore_pos_int_idx < restore_pos_int_length and restore_pos_int[restore_pos_int_idx] == i:
            new_lis.append(virtual.Virtual_Asm("restore", 2, [virtual.Reg(node_int, "int"), virtual.Reg(node_int, 'label')]))
            restore_pos_int_idx += 1
        if store_pos_float_idx < store_pos_float_length and store_pos_float[store_pos_float_idx] == i:
            new_lis.append(virtual.Virtual_Asm("store", 2, [virtual.Reg(node_float, "float"), virtual.Reg(node_float, 'label')]))
            store_pos_float_idx += 1
        if restore_pos_float_idx < restore_pos_float_length and restore_pos_float[restore_pos_float_idx] == i:
            new_lis.append(virtual.Virtual_Asm("restore", 2, [virtual.Reg(node_float, "float"), virtual.Reg(node_float, 'label')]))
            restore_pos_float_idx += 1
        new_lis.append(lis[i])
    
    return new_lis
    
# レジスタ割り当て
# virtual_asmのlistを受け取ってレジスタ割り当て後のvirtual_asmを返す
def regAlloc (lis:List[virtual.Virtual_Asm], int_regs, float_regs) -> List[virtual.Virtual_Asm]:
    # regAllocの前処理
    lis = findNotUsedArgs(lis)

    # 一度spillしたものは二度とspillしないようにするために，spillしたものを記憶しておく
    already_spilled_int = set()
    already_spilled_float = set()
    while True:
        # build: virtual_asmのリストからliveness情報を持つグラフを受け取る
        graph_int, graph_float, def_int, use_int, def_float, use_float = build(lis)

        # spillされる可能性のあるものを格納する
        potential_spill_int = set()
        potential_spill_float = set()
        # その他以下のループで使われる変数の初期化
        stk_int = []
        stk_float = []
        simplified_graph_int = copy.deepcopy(graph_int)
        simplified_graph_float = copy.deepcopy(graph_float)
        # simplify: limit未満の隣接ノードを持つノードを削除してスタックに移動する
        # spill: メモリ上に保持する可能性のある変数を選ぶ
        while True:
            # simplify
            simplified_graph_int, stk_int = simplify(simplified_graph_int, len(int_regs), stk_int)
            simplified_graph_float, stk_float = simplify(simplified_graph_float, len(float_regs), stk_float)
            # 全てのノードがスタックに移動できたら終了
            if simplified_graph_int == {} and simplified_graph_float == {}:
                break
            # spill
            simplified_graph_int, name_int, stk_int = spill(simplified_graph_int, stk_int, already_spilled_int)
            if name_int is not None:
                potential_spill_int.add(name_int)
            simplified_graph_float, name_float, stk_float = spill(simplified_graph_float, stk_float, already_spilled_float)
            if name_float is not None:
                potential_spill_float.add(name_float)
        
        # select: スタックからノードをポップしながら割り当てしていく
        allocation_or_node_int = select(graph_int, stk_int, potential_spill_int, int_regs)
        allocation_or_node_float = select(graph_float, stk_float, potential_spill_float, float_regs)

        if type(allocation_or_node_int) is not str and type(allocation_or_node_float) is not str:
            break # allocation_or_node_int, allocation_or_node_floatが答えになっている
        elif type(allocation_or_node_int) is not str: # floatだけまだallocが終わっていない
            already_spilled_float.add(allocation_or_node_float)
            lis = memoryAlloc(lis, node_float=allocation_or_node_float, def_float=def_float, use_float=use_float)
        elif type(allocation_or_node_float) is not str: # intだけまだallocが終わっていない
            already_spilled_int.add(allocation_or_node_int)
            lis = memoryAlloc(lis, node_int=allocation_or_node_int, def_int=def_int, use_int=use_int)
        else:
            already_spilled_int.add(allocation_or_node_int)
            already_spilled_float.add(allocation_or_node_float)
            lis = memoryAlloc(
                lis,
                node_int=allocation_or_node_int,
                def_int=def_int,
                use_int=use_int,
                node_float=allocation_or_node_float,
                def_float=def_float,
                use_float=use_float,
            )
    
    # 不要な命令を削除する
    allocation_or_node_int, allocation_or_node_float = removeUnnecessaryInstr(lis, allocation_or_node_int, allocation_or_node_float)

    # allocationに従ってlisを書き換える
    for asm in lis:
        for i in range(len(asm.arg_list)):
            if (asm.arg_list[i].typ == "int") and not (isImmediate(asm.arg_list[i].name)) and not (asm.arg_list[i].name in reglist.SPECIAL_INT_REGS):
                asm.arg_list[i] = virtual.Reg(allocation_or_node_int[asm.arg_list[i].name], "int")

    # allocationに従ってlisを書き換える
    for asm in lis:
        for i in range(len(asm.arg_list)):
            if (asm.arg_list[i].typ == "float") and not (isImmediate(asm.arg_list[i].name)) and not (asm.arg_list[i].name in reglist.SPECIAL_FLOAT_REGS):
                asm.arg_list[i] = virtual.Reg(allocation_or_node_float[asm.arg_list[i].name], "float")
    
    return lis

# 関数の引数の割り当てを，実際にcallされるときに渡される順に並び替える最適化
def optimizeAllocOfArgs (lis:List[virtual.Virtual_Asm]) -> List[virtual.Virtual_Asm]:
    # "* args" から引数のレジスタの並びを取得
    arg_regs_int = []
    arg_regs_float = []
    for asm in lis:
        if asm.instr_name == "* args" and asm.arg_list[0].typ == "int":
            arg_regs_int.append(asm.arg_list[0].name)
    for asm in lis:
        if asm.instr_name == "* args" and asm.arg_list[0].typ == "float":
            arg_regs_float.append(asm.arg_list[0].name)
    
    # 引数の割り当て
    len_arg_regs_int = len(arg_regs_int)
    len_arg_regs_float = len(arg_regs_float)
    alloc_int = {}
    alloc_float = {}
    for i in range(len_arg_regs_int):
        alloc_int[arg_regs_int[i]] = "a" + str(len_arg_regs_int - i)
    for i in range(len_arg_regs_float):
        alloc_float[arg_regs_float[i]] = "fa" + str(len_arg_regs_float - i - 1)
    
    # arg_regs_intの中で，a1 ~ anのうち使われていないもの
    not_used_in_arg_regs_int = []
    for i in range(1, len_arg_regs_int+1):
        if "a" + str(i) not in alloc_int:
            not_used_in_arg_regs_int.append("a" + str(i))
    # arg_regs_intで使われているものの中で，a1 ~ anに入らないもの
    used_in_arg_regs_int = []
    for name in arg_regs_int:
        if (name[0] != "a") or not (1 <= int(name[1:]) <= len_arg_regs_int):
            used_in_arg_regs_int.append(name)
    # arg_regs_floatの中で，fa0 ~ a(n-1)のうち使われていないもの
    not_used_in_arg_regs_float = []
    for i in range(len_arg_regs_float):
        if "fa" + str(i) not in alloc_float:
            not_used_in_arg_regs_float.append("fa" + str(i))
    # arg_regs_floatで使われているものの中で，fa0 ~ a(n-1)に入らないもの
    used_in_arg_regs_float = []
    for name in arg_regs_float:
        if (name[0:2] != "fa") or not(0 <= int(name[2:]) <= len_arg_regs_float - 1):
            used_in_arg_regs_float.append(name)
    # 「arg_regs_intの中で，a1 ~ anのうち使われていないもの」を，「arg_regs_intで使われているものの中で，a1 ~ anに入らないもの」に適当にキャストする
    for frm, to in zip(not_used_in_arg_regs_int, used_in_arg_regs_int):
        alloc_int[frm] = to
    # floatも同様
    for frm, to in zip(not_used_in_arg_regs_float, used_in_arg_regs_float):
        alloc_float[frm] = to

    # alloc_intに従ってlisを書き換える
    for asm in lis:
        for i in range(len(asm.arg_list)):
            if asm.arg_list[i].name in alloc_int:
                asm.arg_list[i] = virtual.Reg(alloc_int[asm.arg_list[i].name], "int")

    # alloc_floatに従ってlisを書き換える
    for asm in lis:
        for i in range(len(asm.arg_list)):
            if asm.arg_list[i].name in alloc_float:
                asm.arg_list[i] = virtual.Reg(alloc_float[asm.arg_list[i].name], "float")
        
    return lis







