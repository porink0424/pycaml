#--------------------------------------------------
#
# jumpOpt.py
# 連続してジャンプしている部分は直接ジャンプするように書き換える
#
#--------------------------------------------------

from typing import List, Union
import virtual

# i番目の命令の次の命令がjumpであるかどうかを判定する
# jumpである場合はそのラベル名を返す，そうでなければFalseを返す
def isNextInstrJump(lis:List[virtual.Virtual_Asm], i) -> Union[bool, str]:
    # 次の意味のある命令のidxの取得
    i += 1
    while i < len(lis):
        if ":" in lis[i].instr_name: # ラベルはスキップ
            i += 1
        elif lis[i].instr_name == "nop": # nopはスキップ
            i += 1
        else:
            break
    # 次の意味のある命令がjumpであるかどうか判定
    if i < len(lis) and lis[i].instr_name == "j":
        return lis[i].arg_list[0].name
    else:
        return False

# 指定されたラベルが入っているidxを見つける
# みつからなかった場合Falseを返す
def findLabel(lis:List[virtual.Virtual_Asm], label:str) -> Union[int, bool]:
    i = 0
    while i < len(lis) and lis[i].instr_name != label + ":":
        i += 1
    if i == len(lis): # Labelが見つからなかった場合
        return False
    else:
        return i
    

def jumpOpt(lis:List[virtual.Virtual_Asm]) -> List[virtual.Virtual_Asm]:
    for asm in lis:
        if asm.instr_name == "j":
            label = asm.arg_list[0].name
            while True:
                false_or_label_idx = findLabel(lis, label)
                if type(false_or_label_idx) is int:
                    label_idx = false_or_label_idx
                    false_or_jump_label = isNextInstrJump(lis, label_idx)
                    if type(false_or_jump_label) is str: # jump先の次の命令がジャンプだった場合
                        label = false_or_jump_label
                        continue
                    else: # jump先の次の命令がジャンプではなかった場合
                        break
                else:
                    break
            asm.arg_list[0].name = label
    
    return lis

# jumpと違いbranch命令のラベルはspOpt内で参照されるため，ループのなかではなくループ後に実行される
def branchOpt(lis:List[virtual.Virtual_Asm]) -> List[virtual.Virtual_Asm]:
    for asm in lis:
        if asm.instr_name == "beq" or asm.instr_name == "bge" or asm.instr_name == "blt" or asm.instr_name == "bfeq" or asm.instr_name == "bfle" or asm.instr_name == "bflt":
            label = asm.arg_list[2].name
            while True:
                false_or_label_idx = findLabel(lis, label)
                if type(false_or_label_idx) is int:
                    label_idx = false_or_label_idx
                    false_or_jump_label = isNextInstrJump(lis, label_idx)
                    if type(false_or_jump_label) is str: # jump先の次の命令がジャンプだった場合
                        label = false_or_jump_label
                        continue
                    else: # jump先の次の命令がジャンプではなかった場合
                        break
                else:
                    break
            asm.arg_list[2].name = label

    return lis