#--------------------------------------------------
#
# lwStallOpt.py
# lwでロードするレジスタが直後の命令で使われないように軽いスケジューリングを行う
#
#--------------------------------------------------

import virtual
import liveness
from typing import List

# asm1, asm2が依存している（= 入れ替えると意味がかわってしまう）かどうかを判定する
# 依存するならTrueを返す
def isDependent (asm1, asm2):
    def_int, use_int, def_float, use_float = liveness.getDefAndUseFromVirtualAsm(asm1)
    asm1_def_set = def_int.union(def_float)
    asm1_use_set = use_int.union(use_float)
    def_int, use_int, def_float, use_float = liveness.getDefAndUseFromVirtualAsm(asm2)
    asm2_def_set = def_int.union(def_float)
    asm2_use_set = use_int.union(use_float)

    dependentFlag = False

    # WAWのチェック
    for item in asm1_def_set:
        if item in asm2_def_set:
            dependentFlag = True
            break
    
    # WARのチェック
    for item in asm1_use_set:
        if item in asm2_def_set:
            dependentFlag = True
            break

    # RAWのチェック
    for item in asm1_def_set:
        if item in asm2_use_set:
            dependentFlag = True
            break
    
    return dependentFlag

def lwStallOpt (lis:List[virtual.Virtual_Asm]) -> List[virtual.Virtual_Asm]:
    i = 0
    len_lis = len(lis)
    while i < len_lis - 1:
        # lisの中の2命令を取得
        former = lis[i]
        latter = lis[i+1]

        # former, latterがジャンプ等の特殊な命令でないことを確認
        # swもメモリの読み書きで依存が生じてしまうことがあるので除外
        specific_instrs = {"beq", "bge", "blt", "bfeq", "bfle", "bflt", "j", "ret", "jalr", "ret_unit", "nop", "call", "sw", "fsw", "vsw"}
        if (
            (former.instr_name in specific_instrs) or
            (latter.instr_name in specific_instrs) or
            (":" in former.instr_name) or
            (":" in latter.instr_name)
        ):
            i += 1
            continue

        # lwでロードしたレジスタを直後の命令で使っていないか判定
        is_target = False
        def_int, _, def_float, _ = liveness.getDefAndUseFromVirtualAsm(former)
        former_def_set = def_int.union(def_float)
        _, use_int, _, use_float = liveness.getDefAndUseFromVirtualAsm(latter)
        latter_use_set = use_int.union(use_float)

        for def_reg in former_def_set:
            # formerがlwでありlatterでロードしたレジスタを使っている場合
            if (former.instr_name in {"lw", "flw", "vlw"}) and (def_reg in latter_use_set):
                is_target = True
                break
        
        # 実際にスケジューリングする
        if is_target:
            # まず，formerがformerの一個前の命令と入れ替えることができないか確かめ，できる場合はする
            # formerの前の命令が特殊な命令なら諦める
            if i - 1 >= 0 and not isDependent(lis[i-1], former) and not (
                (lis[i-1].instr_name in specific_instrs) or
                (":" in lis[i-1].instr_name)
            ):
                tmp = lis[i-1]
                lis[i-1] = former
                lis[i] = tmp
                break
            
            # 次に，latterがlatterの一個前の命令と入れ替えることができないか確かめ，できる場合はする
            # latterの後の命令が特殊な命令なら諦める
            elif i + 1 < len(lis) and not isDependent(latter, lis[i+1]) and not (
                (lis[i+1].instr_name in specific_instrs) or
                (":" in lis[i+1].instr_name)
            ):
                tmp = lis[i+1]
                lis[i+1] = latter
                lis[i] = tmp
                break
        
        i += 1
    
    return lis
