#--------------------------------------------------
#
# expand.py
# store, restoreの展開と関数呼び出しの展開
#
#--------------------------------------------------

import virtual
from typing import List, Tuple
import copy
import reglist
import lib

# 関数の中で使われているレジスタの集合
used_regs_set_in_func_int = {
    x : lib.instrs[x]["used_regs_set_int"] for x in lib.instrs
}
used_regs_set_in_func_float = {
    x : lib.instrs[x]["used_regs_set_float"] for x in lib.instrs
}

# used_regs_set_in_funcをセットする関数
def set_used_regs_set_in_func (func_name:str, lis, live_int, live_float):
    global used_regs_set_in_func_int, used_regs_set_in_func_float

    # 関数から別の関数を読んでいる時は追跡が難しいので諦める
    for asm in lis:
        if asm.instr_name in {"j", "jalr", "call", "recv_ret_val_cls_int", "recv_ret_val_cls_float", "just_call_cls_and_jump", "just_call_dir_and_jump", "just_call_cls", "just_call_dir", "recv_ret_val_dir_int", "recv_ret_val_dir_float"}:
            return

    # live_int, live_floatの中に入っている変数の集合を作る
    live_int_set = set()
    live_float_set = set()
    for key in live_int:
        live_int_set |= live_int[key]
    for key in live_float:
        live_float_set |= live_float[key]
    
    used_regs_set_in_func_int[func_name] = live_int_set
    used_regs_set_in_func_float[func_name] = live_float_set


# isFundef: callee側かどうかを判定するフラグ
# virtual_stack: store, restoreした変数の情報を保持しておく仮想的なスタック
def expand (
    lis:List[virtual.Virtual_Asm],
    virtual_stack:List[str],
    isFundef:bool,
    live_int, live_float,
    fundef_ret_asm_list=[]
    ) -> Tuple[List[virtual.Virtual_Asm], List[str]]:

    global used_regs_set_in_func_int, used_regs_set_in_func_float
    
    new_lis = []
    idx = 0

    # callee側の場合、callee-saveのレジスタの退避、自由変数の取り出し、callee-saveレジスタの復元の計算が必要なのでそれを行う
    if isFundef:
        # live_int, live_floatの中に入っている変数の集合を作る
        live_int_set = set()
        live_float_set = set()
        for key in live_int:
            live_int_set |= live_int[key]
        for key in live_float:
            live_float_set |= live_float[key]

        new_lis.append(lis[0]) # 関数のラベルの行
        idx += 1

        # 関数内でつかわれてしまっているレジスタの集合を計算
        fundef_virtual_stack_int = []
        fundef_virtual_stack_float = []
        for item in reglist.INT_REGS_FOR_FUNC[reglist.INT_REGS_FOR_FUNC_RESPONSIBLE_IDX:]:
            if item in live_int_set: # callee-saveなレジスタが使われている場合
                fundef_virtual_stack_int.append(item)
        for item in reglist.FLOAT_REGS_FOR_FUNC[reglist.FLOAT_REGS_FOR_FUNC_RESPONSIBLE_IDX:]:
            if item in live_float_set: # callee-saveなレジスタが使われている場合
                fundef_virtual_stack_float.append(item)
        
        # callee-saveレジスタの退避
        tmp_sp = 0
        for item in fundef_virtual_stack_int:
            tmp_sp -= 4
            new_lis.append(virtual.Virtual_Asm("sw", 3, [virtual.Reg("sp", "int"), virtual.Reg(item, "int"), virtual.Reg(str(tmp_sp), "int")]))
        for item in fundef_virtual_stack_float:
            tmp_sp -= 4
            new_lis.append(virtual.Virtual_Asm("fsw", 3, [virtual.Reg("sp", "int"), virtual.Reg(item, "float"), virtual.Reg(str(tmp_sp), "int")]))
        new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_sp), "int")]))
        
        # callee-saveレジスタの復元のアセンブリを生成（ここでアセンブリを生成しておいて、メインループでretを処理する際、実際に付加する）
        fundef_ret_asm_list = []
        fundef_ret_asm_list.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(-tmp_sp), "int")]))
        for item in reversed(fundef_virtual_stack_float):
            fundef_ret_asm_list.append(virtual.Virtual_Asm("flw", 3, [virtual.Reg(item, "float"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_sp), "int")]))
            tmp_sp += 4
        for item in reversed(fundef_virtual_stack_int):
            fundef_ret_asm_list.append(virtual.Virtual_Asm("lw", 3, [virtual.Reg(item, "int"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_sp), "int")]))
            tmp_sp += 4

        # 自由変数をレジスタに割り当てる
        formal_fv_count = 0
        for asm in lis:
            if asm.instr_name == "* formal_fv":
                formal_fv_count += 1
                if asm.arg_list[0].typ == "int":
                    new_lis.append(virtual.Virtual_Asm("lw", 3, [asm.arg_list[0], virtual.Reg("a0", "int"), virtual.Reg(str(formal_fv_count*4), "int")]))
                if asm.arg_list[0].typ == "float":
                    new_lis.append(virtual.Virtual_Asm("flw", 3, [asm.arg_list[0], virtual.Reg("a0", "int"), virtual.Reg(str(formal_fv_count*4), "int")]))

    # メインループ
    while idx < len(lis):
        asm = lis[idx]

        # storeの展開。ストアした変数の情報はvirtual_stackに保持される
        if asm.instr_name == "store":
            # アセンブリにswを加える
            if asm.arg_list[0].typ == "int":
                new_lis.append(virtual.Virtual_Asm("sw", 3, [virtual.Reg("sp", "int"), asm.arg_list[0], virtual.Reg(str(-(len(virtual_stack)+1)*4), "int")]))
            else:
                new_lis.append(virtual.Virtual_Asm("fsw", 3, [virtual.Reg("sp", "int"), asm.arg_list[0], virtual.Reg(str(-(len(virtual_stack)+1)*4), "int")]))
            # 変数virtual_stackに保存する
            virtual_stack.append(asm.arg_list[1].name)
            idx += 1
        
        # restoreの展開
        elif asm.instr_name == "restore":
            # virtual_stackからスタック上の変数のアドレスを計算する
            i = 0
            while i < len(virtual_stack):
                if virtual_stack[i] == asm.arg_list[1].name:
                    break
                i += 1
            pos = -(i + 1) * 4
            # アセンブリにlwを加える
            if asm.arg_list[0].typ == "int":
                new_lis.append(virtual.Virtual_Asm("lw", 3, [asm.arg_list[0], virtual.Reg("sp", "int"), virtual.Reg(str(pos), "int")]))
            else:
                new_lis.append(virtual.Virtual_Asm("flw", 3, [asm.arg_list[0], virtual.Reg("sp", "int"), virtual.Reg(str(pos), "int")])) 
            idx += 1
        
        # ブランチ命令
        elif asm.instr_name == "beq" or asm.instr_name == "bge" or asm.instr_name == "blt" or asm.instr_name == "bfeq" or asm.instr_name == "bfle" or asm.instr_name == "bflt":
            # labelの末尾についている数字を取り出す
            if_cnt = asm.arg_list[2].name.replace("then", "")
            # then節の行のindexを取得
            then_pos = idx
            while True:
                if lis[then_pos].instr_name == "then" + str(if_cnt) + ":":
                    break
                then_pos += 1
            # ブランチ命令〜then節までのlive情報をスライスする
            live_int_slice = {}
            live_float_slice = {}
            for key in live_int:
                if idx+1 <= key < then_pos:
                    live_int_slice[key - (idx+1)] = live_int[key]
            for key in live_float:
                if idx+1 <= key < then_pos:
                    live_float_slice[key - (idx+1)] = live_float[key]
            # expandの処理
            else_asm, else_virtual_stack = expand(lis[idx+1:then_pos], copy.deepcopy(virtual_stack), False, live_int_slice, live_float_slice, fundef_ret_asm_list)
            # thenとendifで囲まれた部分のアセンブリについても上と同様のことを行う
            endif_pos = then_pos
            while True:
                if lis[endif_pos].instr_name == "endif" + str(if_cnt) + ":":
                    break
                endif_pos += 1
            live_int_slice = {}
            live_float_slice = {}
            for key in live_int:
                if then_pos <= key < endif_pos:
                    live_int_slice[key - then_pos] = live_int[key]
            for key in live_float:
                if then_pos <= key < endif_pos:
                    live_float_slice[key - then_pos] = live_float[key]
            then_asm, then_virtual_stack = expand(lis[then_pos:endif_pos], copy.deepcopy(virtual_stack), False, live_int_slice, live_float_slice, fundef_ret_asm_list)
            
            # stackの共通部分をとる
            virtual_stack = [item for item in else_virtual_stack if item in then_virtual_stack]
            new_lis += [asm] + else_asm + then_asm
            idx = endif_pos

        # ret命令
        elif asm.instr_name == "ret":
            new_lis += [
                virtual.Virtual_Asm(
                    "mv",
                    2,
                    [virtual.Reg("a1", "int"), asm.arg_list[0]]
                ) if asm.arg_list[0].typ == "int"
                else virtual.Virtual_Asm(
                    "fmv",
                    2,
                    [virtual.Reg("fa0", "float"), asm.arg_list[0]]
                ), # 返り値をレジスタに入れる
            ] + fundef_ret_asm_list + [
                virtual.Virtual_Asm("ret", 0, [])
            ]
            idx += 1
        
        # 返り値がなにもないret命令
        elif asm.instr_name == "ret_unit":
            new_lis += fundef_ret_asm_list + [
                virtual.Virtual_Asm("ret", 0, [])
            ]
            idx += 1
        
        # クロージャではない関数呼び出し
        elif asm.instr_name == "just_call_dir":
            # 使用する引数レジスタの数に合わせて配列を作る
            func_args_int = []
            func_args_float = []
            int_idx = 1
            float_idx = 0
            for arg in asm.arg_list[1:]:
                if arg.typ == "int":
                    func_args_int.append("a" + str(int_idx))
                    int_idx += 1
                elif arg.typ == "float":
                    func_args_float.append("fa" + str(float_idx))
                    float_idx += 1
            # spの移動
            if len(virtual_stack) != 0:
                new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(-len(virtual_stack)*4), "int")]))
            # caller-saveでかつ呼び出す関数内で使われているレジスタをスタックに移動
            call_virtual_stack_int = []
            call_virtual_stack_float = []
            live_int_set = live_int[idx]
            live_float_set = live_float[idx]

            if asm.arg_list[0].name in used_regs_set_in_func_int:
                caller_regs_used_in_func_int = [
                    x for x in reglist.INT_REGS_FOR_MAIN[reglist.INT_REGS_FOR_MAIN_RESPONSIBLE_IDX:] if x in used_regs_set_in_func_int[asm.arg_list[0].name]
                ]
                caller_regs_used_in_func_float = [
                    x for x in reglist.FLOAT_REGS_FOR_MAIN[reglist.FLOAT_REGS_FOR_MAIN_RESPONSIBLE_IDX:] if x in used_regs_set_in_func_float[asm.arg_list[0].name]
                ]
            else:
                caller_regs_used_in_func_int = reglist.INT_REGS_FOR_MAIN[reglist.INT_REGS_FOR_MAIN_RESPONSIBLE_IDX:]
                caller_regs_used_in_func_float = reglist.FLOAT_REGS_FOR_MAIN[reglist.FLOAT_REGS_FOR_MAIN_RESPONSIBLE_IDX:]

            for item in caller_regs_used_in_func_int:
                if item in live_int_set:
                    call_virtual_stack_int.append(item)
            for item in caller_regs_used_in_func_float:
                if item in live_float_set:
                    call_virtual_stack_float.append(item)
            tmp_sp = 0
            for item in call_virtual_stack_int:
                tmp_sp -= 4
                new_lis.append(virtual.Virtual_Asm("sw", 3, [virtual.Reg("sp", "int"), virtual.Reg(item, "int"), virtual.Reg(str(tmp_sp), "int")]))
            for item in call_virtual_stack_float:
                tmp_sp -= 4
                new_lis.append(virtual.Virtual_Asm("fsw", 3, [virtual.Reg("sp", "int"), virtual.Reg(item, "float"), virtual.Reg(str(tmp_sp), "int")]))
            if tmp_sp != 0:
                new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_sp), "int")]))
            # 引数を引数レジスタに登録する（スタックに一旦保存 → その後取り出す）
            # mv a1, a3; mv a2, a1というときに事故がおこらないようにするため。
            tmp_idx = -1
            for i in range(float_idx):
                if asm.arg_list[tmp_idx].name != "fa" + str(i):
                    new_lis.append(virtual.Virtual_Asm("fsw", 3, [virtual.Reg("sp", "int"), asm.arg_list[tmp_idx], virtual.Reg(str(tmp_idx * 4), "int")]))
                tmp_idx -= 1
            for i in range(int_idx-1):
                if asm.arg_list[tmp_idx].name != "a" + str(i+1):
                    new_lis.append(virtual.Virtual_Asm("sw", 3, [virtual.Reg("sp", "int"), asm.arg_list[tmp_idx], virtual.Reg(str(tmp_idx * 4), "int")]))
                tmp_idx -= 1
            tmp_idx_2 = -1
            for i in range(float_idx):
                if asm.arg_list[tmp_idx_2].name != "fa" + str(i):
                    new_lis.append(virtual.Virtual_Asm("flw", 3, [virtual.Reg(func_args_float[i], "float"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_idx_2 * 4), "int")]))
                tmp_idx_2 -= 1
            for i in range(int_idx-1):
                if asm.arg_list[tmp_idx_2].name != "a" + str(i+1):
                    new_lis.append(virtual.Virtual_Asm("lw", 3, [virtual.Reg(func_args_int[i], "int"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_idx_2 * 4), "int")]))
                tmp_idx_2 -= 1
            # 関数呼び出し
            new_lis.append(virtual.Virtual_Asm("sw", 3, [virtual.Reg("sp", "int"), virtual.Reg("ra", "int"), virtual.Reg("-4", "int")]))
            new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg("-4", "int")]))
            new_lis.append(virtual.Virtual_Asm("call", 1, [asm.arg_list[0]]))
            new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg("4", "int")]))
            new_lis.append(virtual.Virtual_Asm("lw", 3, [virtual.Reg("ra", "int"), virtual.Reg("sp", "int"), virtual.Reg("-4", "int")]))
            # caller-saveなレジスタをもとに戻す
            if tmp_sp != 0:
                new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(-tmp_sp), "int")]))
            for item in reversed(call_virtual_stack_float):
                new_lis.append(virtual.Virtual_Asm("flw", 3, [virtual.Reg(item, "float"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_sp), "int")]))
                tmp_sp += 4
            for item in reversed(call_virtual_stack_int):
                new_lis.append(virtual.Virtual_Asm("lw", 3, [virtual.Reg(item, "int"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_sp), "int")]))
                tmp_sp += 4
            # spをもとに戻す
            if len(virtual_stack) != 0:
                new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(len(virtual_stack)*4), "int")]))
            idx += 1

        elif asm.instr_name == "just_call_dir_and_jump":
            # 使用する引数レジスタの数に合わせて配列を作る
            func_args_int = []
            func_args_float = []
            int_idx = 1
            float_idx = 0
            for arg in asm.arg_list[1:]:
                if arg.typ == "int":
                    func_args_int.append("a" + str(int_idx))
                    int_idx += 1
                elif arg.typ == "float":
                    func_args_float.append("fa" + str(float_idx))
                    float_idx += 1
            # 引数を引数レジスタに登録する（スタックに一旦保存 → その後取り出す）
            # mv a1, a3; mv a2, a1というときに事故がおこらないようにするため。
            tmp_idx = -1
            for i in range(float_idx):
                if asm.arg_list[tmp_idx].name != "fa" + str(i):
                    new_lis.append(virtual.Virtual_Asm("fsw", 3, [virtual.Reg("sp", "int"), asm.arg_list[tmp_idx], virtual.Reg(str(tmp_idx * 4), "int")]))
                tmp_idx -= 1
            for i in range(int_idx-1):
                if asm.arg_list[tmp_idx].name != "a" + str(i+1):
                    new_lis.append(virtual.Virtual_Asm("sw", 3, [virtual.Reg("sp", "int"), asm.arg_list[tmp_idx], virtual.Reg(str(tmp_idx * 4), "int")]))
                tmp_idx -= 1
            tmp_idx_2 = -1
            for i in range(float_idx):
                if asm.arg_list[tmp_idx_2].name != "fa" + str(i):
                    new_lis.append(virtual.Virtual_Asm("flw", 3, [virtual.Reg(func_args_float[i], "float"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_idx_2 * 4), "int")]))
                tmp_idx_2 -= 1
            for i in range(int_idx-1):
                if asm.arg_list[tmp_idx_2].name != "a" + str(i+1):
                    new_lis.append(virtual.Virtual_Asm("lw", 3, [virtual.Reg(func_args_int[i], "int"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_idx_2 * 4), "int")]))
                tmp_idx_2 -= 1
            # 関数呼び出し
            new_lis += fundef_ret_asm_list + [
                virtual.Virtual_Asm("j", 1, [asm.arg_list[0]]) # このあとの命令に戻ってくる必要がないので、ただのjでOK
            ]
            idx += 1

        elif asm.instr_name == "recv_ret_val_dir_int" or asm.instr_name == "recv_ret_val_dir_float":
            # 使用する引数レジスタの数に合わせて配列を作る
            func_args_int = []
            func_args_float = []
            int_idx = 1
            float_idx = 0
            for arg in asm.arg_list[2:]:
                if arg.typ == "int":
                    func_args_int.append("a" + str(int_idx))
                    int_idx += 1
                elif arg.typ == "float":
                    func_args_float.append("fa" + str(float_idx))
                    float_idx += 1
            # spの移動
            if len(virtual_stack) != 0:
                new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(-len(virtual_stack)*4), "int")]))
            # caller-saveでかつ呼び出す関数内で使われているレジスタをスタックに移動
            call_virtual_stack_int = []
            call_virtual_stack_float = []
            live_int_set = live_int[idx]
            live_float_set = live_float[idx]

            if asm.arg_list[1].name in used_regs_set_in_func_int:
                caller_regs_used_in_func_int = [
                    x for x in reglist.INT_REGS_FOR_MAIN[reglist.INT_REGS_FOR_MAIN_RESPONSIBLE_IDX:] if x in used_regs_set_in_func_int[asm.arg_list[1].name]
                ]
                caller_regs_used_in_func_float = [
                    x for x in reglist.FLOAT_REGS_FOR_MAIN[reglist.FLOAT_REGS_FOR_MAIN_RESPONSIBLE_IDX:] if x in used_regs_set_in_func_float[asm.arg_list[1].name]
                ]
            else:
                caller_regs_used_in_func_int = reglist.INT_REGS_FOR_MAIN[reglist.INT_REGS_FOR_MAIN_RESPONSIBLE_IDX:]
                caller_regs_used_in_func_float = reglist.FLOAT_REGS_FOR_MAIN[reglist.FLOAT_REGS_FOR_MAIN_RESPONSIBLE_IDX:]

            for item in caller_regs_used_in_func_int:
                if item in live_int_set:
                    call_virtual_stack_int.append(item)
            for item in caller_regs_used_in_func_float:
                if item in live_float_set:
                    call_virtual_stack_float.append(item)
            tmp_sp = 0
            for item in call_virtual_stack_int:
                tmp_sp -= 4
                new_lis.append(virtual.Virtual_Asm("sw", 3, [virtual.Reg("sp", "int"), virtual.Reg(item, "int"), virtual.Reg(str(tmp_sp), "int")]))
            for item in call_virtual_stack_float:
                tmp_sp -= 4
                new_lis.append(virtual.Virtual_Asm("fsw", 3, [virtual.Reg("sp", "int"), virtual.Reg(item, "float"), virtual.Reg(str(tmp_sp), "int")]))
            if tmp_sp != 0:
                new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_sp), "int")]))
            # 引数を引数レジスタに登録する（スタックに一旦保存 → その後取り出す）
            # mv a1, a3; mv a2, a1というときに事故がおこらないようにするため。
            tmp_idx = -1
            for i in range(float_idx):
                if asm.arg_list[tmp_idx].name != "fa" + str(i):
                    new_lis.append(virtual.Virtual_Asm("fsw", 3, [virtual.Reg("sp", "int"), asm.arg_list[tmp_idx], virtual.Reg(str(tmp_idx * 4), "int")]))
                tmp_idx -= 1
            for i in range(int_idx-1):
                if asm.arg_list[tmp_idx].name != "a" + str(i+1):
                    new_lis.append(virtual.Virtual_Asm("sw", 3, [virtual.Reg("sp", "int"), asm.arg_list[tmp_idx], virtual.Reg(str(tmp_idx * 4), "int")]))
                tmp_idx -= 1
            tmp_idx_2 = -1
            for i in range(float_idx):
                if asm.arg_list[tmp_idx_2].name != "fa" + str(i):
                    new_lis.append(virtual.Virtual_Asm("flw", 3, [virtual.Reg(func_args_float[i], "float"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_idx_2 * 4), "int")]))
                tmp_idx_2 -= 1
            for i in range(int_idx-1):
                if asm.arg_list[tmp_idx_2].name != "a" + str(i+1):
                    new_lis.append(virtual.Virtual_Asm("lw", 3, [virtual.Reg(func_args_int[i], "int"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_idx_2 * 4), "int")]))
                tmp_idx_2 -= 1
            # 関数呼び出し
            new_lis.append(virtual.Virtual_Asm("sw", 3, [virtual.Reg("sp", "int"), virtual.Reg("ra", "int"), virtual.Reg("-4", "int")]))
            new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg("-4", "int")]))
            new_lis.append(virtual.Virtual_Asm("call", 1, [asm.arg_list[1]]))
            new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg("4", "int")]))
            new_lis.append(virtual.Virtual_Asm("lw", 3, [virtual.Reg("ra", "int"), virtual.Reg("sp", "int"), virtual.Reg("-4", "int")]))
            # 関数が返ってきたら一旦f4 or x4に退避させる
            if asm.instr_name == "recv_ret_val_dir_int":
                new_lis.append(virtual.Virtual_Asm("mv", 2, [virtual.Reg("x4", "int"), virtual.Reg("a1", "int")]))
            elif asm.instr_name == "recv_ret_val_dir_float":
                new_lis.append(virtual.Virtual_Asm("fmv", 2, [virtual.Reg("f4", "float"), virtual.Reg("fa0", "float")]))
            # caller-saveなレジスタをもとに戻す
            if tmp_sp != 0:
                new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(-tmp_sp), "int")]))
            for item in reversed(call_virtual_stack_float):
                new_lis.append(virtual.Virtual_Asm("flw", 3, [virtual.Reg(item, "float"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_sp), "int")]))
                tmp_sp += 4
            for item in reversed(call_virtual_stack_int):
                new_lis.append(virtual.Virtual_Asm("lw", 3, [virtual.Reg(item, "int"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_sp), "int")]))
                tmp_sp += 4
            # spをもとに戻す
            if len(virtual_stack) != 0:
                new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(len(virtual_stack)*4), "int")]))
            idx += 1
            # 引数受け取り
            if asm.instr_name == "recv_ret_val_dir_int":
                new_lis.append(virtual.Virtual_Asm("mv", 2, [asm.arg_list[0], virtual.Reg("x4", "int")]))
            elif asm.instr_name == "recv_ret_val_dir_float":
                new_lis.append(virtual.Virtual_Asm("fmv", 2, [asm.arg_list[0], virtual.Reg("f4", "float")]))

        elif asm.instr_name == "just_call_cls":
            # 使用する引数レジスタの数に合わせて配列を作る
            func_args_int = []
            func_args_float = []
            int_idx = 1
            float_idx = 0
            for arg in asm.arg_list[1:]:
                if arg.typ == "int":
                    func_args_int.append("a" + str(int_idx))
                    int_idx += 1
                elif arg.typ == "float":
                    func_args_float.append("fa" + str(float_idx))
                    float_idx += 1
            # spの移動
            if len(virtual_stack) != 0:
                new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(-len(virtual_stack)*4), "int")]))
            # caller-saveなレジスタをスタックに移動
            call_virtual_stack_int = []
            call_virtual_stack_float = []
            live_int_set = live_int[idx]
            live_float_set = live_float[idx]
            for item in reglist.INT_REGS_FOR_MAIN[reglist.INT_REGS_FOR_MAIN_RESPONSIBLE_IDX:]:
                if item in live_int_set:
                    call_virtual_stack_int.append(item)
            for item in reglist.FLOAT_REGS_FOR_MAIN[reglist.FLOAT_REGS_FOR_MAIN_RESPONSIBLE_IDX:]:
                if item in live_float_set:
                    call_virtual_stack_float.append(item)
            tmp_sp = 0
            for item in call_virtual_stack_int:
                tmp_sp -= 4
                new_lis.append(virtual.Virtual_Asm("sw", 3, [virtual.Reg("sp", "int"), virtual.Reg(item, "int"), virtual.Reg(str(tmp_sp), "int")]))
            for item in call_virtual_stack_float:
                tmp_sp -= 4
                new_lis.append(virtual.Virtual_Asm("fsw", 3, [virtual.Reg("sp", "int"), virtual.Reg(item, "float"), virtual.Reg(str(tmp_sp), "int")]))
            if tmp_sp != 0:
                new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_sp), "int")]))
            # 関数のラベルをクロージャから取り出す
            new_lis.append(virtual.Virtual_Asm("lw", 3, [virtual.Reg("x4", "int"), asm.arg_list[0], virtual.Reg("0", "int")]))
            new_lis.append(virtual.Virtual_Asm("mv", 2, [virtual.Reg("a0", "int"), asm.arg_list[0]]))
            # 引数を引数レジスタに登録する（スタックに一旦保存 → その後取り出す）
            # mv a1, a3; mv a2, a1というときに事故がおこらないようにするため。
            tmp_idx = -1
            for i in range(float_idx):
                if asm.arg_list[tmp_idx].name != "fa" + str(i):
                    new_lis.append(virtual.Virtual_Asm("fsw", 3, [virtual.Reg("sp", "int"), asm.arg_list[tmp_idx], virtual.Reg(str(tmp_idx * 4), "int")]))
                tmp_idx -= 1
            for i in range(int_idx-1):
                if asm.arg_list[tmp_idx].name != "a" + str(i+1):
                    new_lis.append(virtual.Virtual_Asm("sw", 3, [virtual.Reg("sp", "int"), asm.arg_list[tmp_idx], virtual.Reg(str(tmp_idx * 4), "int")]))
                tmp_idx -= 1
            tmp_idx_2 = -1
            for i in range(float_idx):
                if asm.arg_list[tmp_idx_2].name != "fa" + str(i):
                    new_lis.append(virtual.Virtual_Asm("flw", 3, [virtual.Reg(func_args_float[i], "float"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_idx_2 * 4), "int")]))
                tmp_idx_2 -= 1
            for i in range(int_idx-1):
                if asm.arg_list[tmp_idx_2].name != "a" + str(i+1):
                    new_lis.append(virtual.Virtual_Asm("lw", 3, [virtual.Reg(func_args_int[i], "int"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_idx_2 * 4), "int")]))
                tmp_idx_2 -= 1
            # 関数呼び出し
            new_lis.append(virtual.Virtual_Asm("sw", 3, [virtual.Reg("sp", "int"), virtual.Reg("ra", "int"), virtual.Reg("-4", "int")]))
            new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg("-4", "int")]))
            new_lis.append(virtual.Virtual_Asm("jalr", 2, [virtual.Reg("x4", "int")]))
            new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg("4", "int")]))
            new_lis.append(virtual.Virtual_Asm("lw", 3, [virtual.Reg("ra", "int"), virtual.Reg("sp", "int"), virtual.Reg("-4", "int")]))
            # caller-saveなレジスタをもとに戻す
            if tmp_sp != 0:
                new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(-tmp_sp), "int")]))
            for item in reversed(call_virtual_stack_float):
                new_lis.append(virtual.Virtual_Asm("flw", 3, [virtual.Reg(item, "float"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_sp), "int")]))
                tmp_sp += 4
            for item in reversed(call_virtual_stack_int):
                new_lis.append(virtual.Virtual_Asm("lw", 3, [virtual.Reg(item, "int"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_sp), "int")]))
                tmp_sp += 4
            # spをもとに戻す
            if len(virtual_stack) != 0:
                new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(len(virtual_stack)*4), "int")]))
            idx += 1

        elif asm.instr_name == "just_call_cls_and_jump":
            # 使用する引数レジスタの数に合わせて配列を作る
            func_args_int = []
            func_args_float = []
            int_idx = 1
            float_idx = 0
            for arg in asm.arg_list[1:]:
                if arg.typ == "int":
                    func_args_int.append("a" + str(int_idx))
                    int_idx += 1
                elif arg.typ == "float":
                    func_args_float.append("fa" + str(float_idx))
                    float_idx += 1
            # 関数のラベルをクロージャから取り出す
            new_lis.append(virtual.Virtual_Asm("lw", 3, [virtual.Reg("x4", "int"), asm.arg_list[0], virtual.Reg("0", "int")]))
            new_lis.append(virtual.Virtual_Asm("mv", 2, [virtual.Reg("a0", "int"), asm.arg_list[0]]))
            # 引数を引数レジスタに登録する（スタックに一旦保存 → その後取り出す）
            # mv a1, a3; mv a2, a1というときに事故がおこらないようにするため。
            tmp_idx = -1
            for i in range(float_idx):
                if asm.arg_list[tmp_idx].name != "fa" + str(i):
                    new_lis.append(virtual.Virtual_Asm("fsw", 3, [virtual.Reg("sp", "int"), asm.arg_list[tmp_idx], virtual.Reg(str(tmp_idx * 4), "int")]))
                tmp_idx -= 1
            for i in range(int_idx-1):
                if asm.arg_list[tmp_idx].name != "a" + str(i+1):
                    new_lis.append(virtual.Virtual_Asm("sw", 3, [virtual.Reg("sp", "int"), asm.arg_list[tmp_idx], virtual.Reg(str(tmp_idx * 4), "int")]))
                tmp_idx -= 1
            tmp_idx_2 = -1
            for i in range(float_idx):
                if asm.arg_list[tmp_idx_2].name != "fa" + str(i):
                    new_lis.append(virtual.Virtual_Asm("flw", 3, [virtual.Reg(func_args_float[i], "float"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_idx_2 * 4), "int")]))
                tmp_idx_2 -= 1
            for i in range(int_idx-1):
                if asm.arg_list[tmp_idx_2].name != "a" + str(i+1):
                    new_lis.append(virtual.Virtual_Asm("lw", 3, [virtual.Reg(func_args_int[i], "int"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_idx_2 * 4), "int")]))
                tmp_idx_2 -= 1
            # 関数呼び出し
            new_lis += fundef_ret_asm_list + [
                virtual.Virtual_Asm("jalr", 3, [virtual.Reg("x0", "int"), virtual.Reg("x4", "int"), virtual.Reg("0", "int")])
            ]
            idx += 1

        elif asm.instr_name == "recv_ret_val_cls_int" or asm.instr_name == "recv_ret_val_cls_float":
            # 使用する引数レジスタの数に合わせて配列を作る
            func_args_int = []
            func_args_float = []
            int_idx = 1
            float_idx = 0
            for arg in asm.arg_list[2:]:
                if arg.typ == "int":
                    func_args_int.append("a" + str(int_idx))
                    int_idx += 1
                elif arg.typ == "float":
                    func_args_float.append("fa" + str(float_idx))
                    float_idx += 1
            # spの移動
            if len(virtual_stack) != 0:
                new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(-len(virtual_stack)*4), "int")]))
            # caller-saveなレジスタをスタックに移動
            call_virtual_stack_int = []
            call_virtual_stack_float = []
            live_int_set = live_int[idx]
            live_float_set = live_float[idx]
            for item in reglist.INT_REGS_FOR_MAIN[reglist.INT_REGS_FOR_MAIN_RESPONSIBLE_IDX:]:
                if item in live_int_set:
                    call_virtual_stack_int.append(item)
            for item in reglist.FLOAT_REGS_FOR_MAIN[reglist.FLOAT_REGS_FOR_MAIN_RESPONSIBLE_IDX:]:
                if item in live_float_set:
                    call_virtual_stack_float.append(item)
            tmp_sp = 0
            for item in call_virtual_stack_int:
                tmp_sp -= 4
                new_lis.append(virtual.Virtual_Asm("sw", 3, [virtual.Reg("sp", "int"), virtual.Reg(item, "int"), virtual.Reg(str(tmp_sp), "int")]))
            for item in call_virtual_stack_float:
                tmp_sp -= 4
                new_lis.append(virtual.Virtual_Asm("fsw", 3, [virtual.Reg("sp", "int"), virtual.Reg(item, "float"), virtual.Reg(str(tmp_sp), "int")]))
            if tmp_sp != 0:
                new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_sp), "int")]))
            # 関数のラベルをクロージャから取り出す
            new_lis.append(virtual.Virtual_Asm("lw", 3, [virtual.Reg("x4", "int"), asm.arg_list[1], virtual.Reg("0", "int")]))
            new_lis.append(virtual.Virtual_Asm("mv", 2, [virtual.Reg("a0", "int"), asm.arg_list[1]]))
            # 引数を引数レジスタに登録する（スタックに一旦保存 → その後取り出す）
            # mv a1, a3; mv a2, a1というときに事故がおこらないようにするため。
            tmp_idx = -1
            for i in range(float_idx):
                if asm.arg_list[tmp_idx].name != "fa" + str(i):
                    new_lis.append(virtual.Virtual_Asm("fsw", 3, [virtual.Reg("sp", "int"), asm.arg_list[tmp_idx], virtual.Reg(str(tmp_idx * 4), "int")]))
                tmp_idx -= 1
            for i in range(int_idx-1):
                if asm.arg_list[tmp_idx].name != "a" + str(i+1):
                    new_lis.append(virtual.Virtual_Asm("sw", 3, [virtual.Reg("sp", "int"), asm.arg_list[tmp_idx], virtual.Reg(str(tmp_idx * 4), "int")]))
                tmp_idx -= 1
            tmp_idx_2 = -1
            for i in range(float_idx):
                if asm.arg_list[tmp_idx_2].name != "fa" + str(i):
                    new_lis.append(virtual.Virtual_Asm("flw", 3, [virtual.Reg(func_args_float[i], "float"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_idx_2 * 4), "int")]))
                tmp_idx_2 -= 1
            for i in range(int_idx-1):
                if asm.arg_list[tmp_idx_2].name != "a" + str(i+1):
                    new_lis.append(virtual.Virtual_Asm("lw", 3, [virtual.Reg(func_args_int[i], "int"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_idx_2 * 4), "int")]))
                tmp_idx_2 -= 1
            # 関数呼び出し
            new_lis.append(virtual.Virtual_Asm("sw", 3, [virtual.Reg("sp", "int"), virtual.Reg("ra", "int"), virtual.Reg("-4", "int")]))
            new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg("-4", "int")]))
            new_lis.append(virtual.Virtual_Asm("jalr", 2, [virtual.Reg("x4", "int")]))
            new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg("4", "int")]))
            new_lis.append(virtual.Virtual_Asm("lw", 3, [virtual.Reg("ra", "int"), virtual.Reg("sp", "int"), virtual.Reg("-4", "int")]))
            # 関数が返ってきたら一旦f4 or x4に退避させる
            if asm.instr_name == "recv_ret_val_cls_int":
                new_lis.append(virtual.Virtual_Asm("mv", 2, [virtual.Reg("x4", "int"), virtual.Reg("a1", "int")]))
            elif asm.instr_name == "recv_ret_val_cls_float":
                new_lis.append(virtual.Virtual_Asm("fmv", 2, [virtual.Reg("f4", "float"), virtual.Reg("fa0", "float")]))
            # caller-saveなレジスタをもとに戻す
            if tmp_sp != 0:
                new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(-tmp_sp), "int")]))
            for item in reversed(call_virtual_stack_float):
                new_lis.append(virtual.Virtual_Asm("flw", 3, [virtual.Reg(item, "float"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_sp), "int")]))
                tmp_sp += 4
            for item in reversed(call_virtual_stack_int):
                new_lis.append(virtual.Virtual_Asm("lw", 3, [virtual.Reg(item, "int"), virtual.Reg("sp", "int"), virtual.Reg(str(tmp_sp), "int")]))
                tmp_sp += 4
            # spをもとに戻す
            if len(virtual_stack) != 0:
                new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(len(virtual_stack)*4), "int")]))
            idx += 1
            # 引数受け取り
            if asm.instr_name == "recv_ret_val_cls_int":
                new_lis.append(virtual.Virtual_Asm("mv", 2, [asm.arg_list[0], virtual.Reg("x4", "int")]))
            elif asm.instr_name == "recv_ret_val_cls_float":
                new_lis.append(virtual.Virtual_Asm("fmv", 2, [asm.arg_list[0], virtual.Reg("f4", "float")]))
        elif asm.instr_name == "* args" or asm.instr_name == "* not used args" or asm.instr_name == "* formal_fv":
            idx += 1
        
        # その他の命令はそのまま
        else:
            new_lis.append(asm)
            idx += 1
    
    return new_lis, virtual_stack
