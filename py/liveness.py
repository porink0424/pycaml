#--------------------------------------------------
#
# liveness.py
# List[virtual.Virtual_Asm]の生存解析を行う
#
# 実装の方針：
# 命令iが定義する変数の集合をdef[i]、命令iが使用する変数の集合をuse[i]としたときに、各命令iについて次の式で生存変数live[i]を計算する：
# live[i] = ∪_{j in succ(i)} (live[j] \ def[j]) ∪ use[j]
# 全てのlive[i]が収束するまで繰り返し計算する。succ(i)は命令iの後続命令の集合である。
#
#--------------------------------------------------

from typing import List, Set, Tuple, Dict
import virtual
import re
import reglist
import error

# regのtypを判別して、対応するdef集合にregを追加する
def AddToDef (reg:virtual.Reg, def_int:Set[str], def_float:Set[str]):
    if reg.typ == "float":
        if reg.name in reglist.SPECIAL_FLOAT_REGS: # 定数レジスタなど特別な用途を持つレジスタは解析に含めない
            return
        def_float.add(reg.name)
    elif reg.typ == "label":
        pass
    else:
        if reg.name in reglist.SPECIAL_INT_REGS: # 定数レジスタなど特別な用途を持つレジスタは解析に含めない
            return
        def_int.add(reg.name)

# regのtypを判別して、対応するuse集合にregを追加する
def AddToUse (reg:virtual.Reg, use_int:Set[str], use_float:Set[str]):
    if reg.typ == "float":
        if reg.name in reglist.SPECIAL_FLOAT_REGS: # 定数レジスタなど特別な用途を持つレジスタは解析に含めない
            return
        use_float.add(reg.name)
    elif reg.typ == "label":
        pass
    else:
        if reg.name in reglist.SPECIAL_INT_REGS: # 定数レジスタなど特別な用途を持つレジスタは解析に含めない
            return
        if re.compile(r'^-?\d+$').search(reg.name): # 即値レジスタは解析に含めない
            return
        use_int.add(reg.name)

# 1つのvirtual.Virtual_Asmから，その命令が定義する整数変数の集合def_int, その命令が使用する整数変数の集合use_int,
# その命令が定義する小数変数の集合def_float, その命令が使用する小数変数の集合use_floatをこの順で返す。
def getDefAndUseFromVirtualAsm (asm:virtual.Virtual_Asm) -> Tuple[Set[str]]:
    def_int, use_int, def_float, use_float = set(), set(), set(), set()

    # a := bの形式の命令
    if asm.instr_name in {"lw", "flw", "mv", "fmv", "fmv.w.x", "fneg", "fabs", "fsqrt", "addi", "slli", "srli", "neg", "fcvt.s.w", "fcvt.w.s"}:
        AddToDef(asm.arg_list[0], def_int, def_float)
        AddToUse(asm.arg_list[1], use_int, use_float)
    
    # a := b + cの形式の命令
    elif asm.instr_name in {"add", "sub", "fadd", "fsub", "fmul", "fdiv", "feq", "fle", "flt", "sll", "srl", "fsgnj", "fsgnjx", "fsgnjn"}:
        AddToDef(asm.arg_list[0], def_int, def_float)
        AddToUse(asm.arg_list[1], use_int, use_float)
        AddToUse(asm.arg_list[2], use_int, use_float)
    
    # b + cの形式の命令
    elif asm.instr_name in {"sw", "fsw", "beq", "bge", "blt", "bfeq", "bfle", "bflt"}:
        AddToUse(asm.arg_list[0], use_int, use_float)
        AddToUse(asm.arg_list[1], use_int, use_float)
    
    # a := 何らかの値 の形式の命令
    elif asm.instr_name in {"li", "fli", "restore", "* args", "la", "* formal_fv", "lwi", "flwi"}:
        AddToDef(asm.arg_list[0], def_int, def_float)
    
    # a の形式の命令
    elif asm.instr_name in {"j", "ret", "store", "jalr", "* not used args", "swi", "fswi"}:
        if len(asm.arg_list) > 0:
            AddToUse(asm.arg_list[0], use_int, use_float)

    elif asm.instr_name in {"ret_unit"}:
        pass

    # a := b1, b2, ... , bnの形式の命令
    elif asm.instr_name in {"recv_ret_val_cls_int", "recv_ret_val_cls_float", "recv_ret_val_dir_int", "recv_ret_val_dir_float"}:
        AddToDef(asm.arg_list[0], def_int, def_float)
        for i in range(1, len(asm.arg_list)):
            AddToUse(asm.arg_list[i], use_int, use_float)
    
    # b1, b2, ... , bnの形式の命令
    elif asm.instr_name in {"just_call_cls", "just_call_dir", "just_call_dir_and_jump", "just_call_cls_and_jump"}:
        for i in range(len(asm.arg_list)):
            AddToUse(asm.arg_list[i], use_int, use_float)
    
    # a1 := b , a2 := b , an := bの形式の命令
    elif asm.instr_name in {"vlw"}:
        for i in range(1, len(asm.arg_list) - 1):
            AddToDef(asm.arg_list[i], def_int, def_float)
        AddToUse(asm.arg_list[0], use_int, use_float)
    
    # 全てuseする形式の命令
    elif asm.instr_name in {"vsw"}:
        for i in range(len(asm.arg_list) - 1):
            AddToUse(asm.arg_list[i], use_int, use_float)

    elif ":" in asm.instr_name: # labelは生存解析に含めない
        pass
    elif asm.instr_name in {"nop", "call"}: # 生存解析に含めない命令
        pass
    else:
        error.error("Invalid instruction: {}.".format(asm.instr_name))

    return def_int, use_int, def_float, use_float

# ラベルの行やコメントアウトの行はskipしたうえで、now_idxの直後の命令のidxを返す
def getImmediatelySuccInstrIdx (now_idx:int, asm_length:int, lis:List[virtual.Virtual_Asm]) -> List[int]:
    j = now_idx + 1
    while j < asm_length and ((":" in lis[j].instr_name) or ("#" in lis[j].instr_name)): # ラベルの行やコメントアウトの行はskip
        j += 1
    if j == asm_length: # lisの最後に達している
        return []
    else:
        return [j]

# List[virtual.Virtual_Asm]のそれぞれのVirtual_Asmに対して、後続命令を計算する
# 返り値は
#   命令のidx => 後続命令のidxの配列
# という要素が入った辞書succ_instrs
def getSuccInstrsFromVirtualAsms (lis:List[virtual.Virtual_Asm]) -> Dict[int, List[int]]:
    asm_length = len(lis)

    # ラベルがどこにあるかを先に計算しておく
    label_pos = {}
    for i in range(asm_length):
        asm = lis[i]
        if ":" in asm.instr_name:
            label_pos[asm.instr_name] = i

    # 後続の命令の計算
    succ_instrs = {}
    for i in range(asm_length):
        asm = lis[i]
        if ":" in asm.instr_name: # ラベルの行に関しては無視
            continue
        elif "#" in asm.instr_name: # コメントアウトの行に関しては無視
            continue
        if asm.instr_name in {"beq", "bge", "blt", "bfeq", "bfle", "bflt"}: # 2通りの後続命令がある命令
            label_name = asm.arg_list[2].name
            label_idx = label_pos[label_name + ":"]
            succ_instrs[i] = getImmediatelySuccInstrIdx(i, asm_length, lis) + getImmediatelySuccInstrIdx(label_idx, asm_length, lis)
        elif asm.instr_name in {"j"}: # ジャンプ命令
            label_name = asm.arg_list[0].name
            label_idx = label_pos[label_name + ":"]
            succ_instrs[i] = getImmediatelySuccInstrIdx(label_idx, asm_length, lis)
        else: # 次の命令に進むだけの命令
            succ_instrs[i] = getImmediatelySuccInstrIdx(i, asm_length, lis)

    return succ_instrs

# ラベルやコメントアウトの行以外の有効な命令のidxのリストの取得
def getInstrIdxList (lis:List[virtual.Virtual_Asm]) -> List[int]:
    instr_idx_list = []
    asm_length = len(lis)
    for i in range(asm_length):
        asm = lis[i]
        if (":" not in asm.instr_name) and ("#" not in asm.instr_name):
            instr_idx_list.append(i)
    return instr_idx_list

# 生存解析
def AnalyzeLiveness (lis:List[virtual.Virtual_Asm]) -> Tuple[Dict[int, List[str]]]:
    # ラベルやコメントアウトの行以外の有効な命令のidxのリスト
    instr_idx_list = getInstrIdxList(lis)

    length_instrs = len(instr_idx_list)
    if length_instrs == 0: # 有効な命令がなければ空を返す
        return {}, {}

    # 生存解析に必要なdef,useの集合や後続命令の集合を取得
    def_int, use_int, def_float, use_float = {}, {}, {}, {}
    for i in instr_idx_list:
        asm = lis[i]
        def_int[i], use_int[i], def_float[i], use_float[i] = getDefAndUseFromVirtualAsm(asm)
    succ_instrs = getSuccInstrsFromVirtualAsms(lis)

    # 実際の生存変数の計算
    live_int = {
        i : set() for i in instr_idx_list # 初期化
    }
    live_float = {
        i : set() for i in instr_idx_list # 初期化
    }
    idx = length_instrs - 1 # 逆順で計算するため、instr_idx_listの最後の要素のidxを最初にとって、ループ内でデクリメントしていく
    no_change_int_count = 0 # live_intが変化しなかった連続の回数
    no_change_float_count = 0 # live_floatが変化しなかった連続の回数

    while not (no_change_int_count == length_instrs and no_change_float_count == length_instrs): # 更新式に従って更新しても、liveが変わらないのがlength_instrs回続いたら解析終了
        # instr_idxはぐるぐるinstr_idx_listの中を回り続ける
        instr_idx = instr_idx_list[idx]
        # 計算式に従ってliveを更新
        pre_live_int_of_instr_idx = live_int[instr_idx]
        pre_live_float_of_instr_idx = live_float[instr_idx]
        for succ_instr_idx in succ_instrs[instr_idx]:
            live_int[instr_idx] |= (live_int[succ_instr_idx] - def_int[succ_instr_idx]) | use_int[succ_instr_idx]
            live_float[instr_idx] |= (live_float[succ_instr_idx] - def_float[succ_instr_idx]) | use_float[succ_instr_idx]
        # 更新によってliveが変わっていなければcountをインクリメント
        if pre_live_int_of_instr_idx == live_int[instr_idx]:
            no_change_int_count += 1
        else:
            no_change_int_count = 0
        if pre_live_float_of_instr_idx == live_float[instr_idx]:
            no_change_float_count += 1
        else:
            no_change_float_count = 0
        # idxをデクリメント
        idx -= 1
        idx = idx % length_instrs
    
    return live_int, live_float, def_int, use_int, def_float, use_float
