#--------------------------------------------------
#
# constFold.py
# グローバル変数の配列の先頭アドレスが確定されたことによって、整数の定数畳み込みができるので、それを行う
#
#--------------------------------------------------

import virtual
import re
from typing import List

# グローバル変数の配列の先頭アドレスが確定されたことによって整数の定数畳み込みができる
def constFold (lis:List[virtual.Virtual_Asm]) -> List[virtual.Virtual_Asm]:
    # 変数→値への写像
    constEnv = {}

    # lisのインデックス
    i = 0

    # new_lisに新しく命令列を作り、これを関数の返り値として返す
    new_lis = []

    # メインループ
    while i < len(lis):
        asm = lis[i]

        # 変数→値の情報を登録する
        if asm.instr_name == "li":
            constEnv[asm.arg_list[0].name] = asm.arg_list[1].name

        # negの第二引数がconstEnvに登録されていれば、その値に負号をつけた値で第一引数をconstEnvに登録することができる
        elif asm.instr_name == "neg":
            if asm.arg_list[1].name in constEnv:
                constEnv[asm.arg_list[0].name] = "-" + constEnv[asm.arg_list[1].name]
        
        # 移動元の変数が定数だったら移動先の変数も定数
        elif asm.instr_name == "mv":
            if asm.arg_list[1].name in constEnv:
                constEnv[asm.arg_list[0].name] = constEnv[asm.arg_list[1].name]

        # Get命令
        elif asm.instr_name == "slli" and re.match(r"^get1\..*", asm.arg_list[0].name) != None:
            if asm.arg_list[1].name in constEnv and lis[i+1].arg_list[1].name in constEnv: # Get命令の2つの引数がどちらも定数だった場合、slli,add,lw_or_flwを一つのlw_or_flwにすることができる
                var1 = constEnv[lis[i+1].arg_list[1].name]
                var2 = constEnv[asm.arg_list[1].name]
                new_lis.append(virtual.Virtual_Asm(lis[i+2].instr_name + "i", 2, [lis[i+2].arg_list[0], virtual.Reg(str(int(var1) + int(var2) * 4), "int")]))
                i += 3
                continue
            elif lis[i+1].arg_list[1].name in constEnv: # 1番目の引数だけ定数の場合、slli,add,lw_or_flwのうちaddは減らすことができる
                var1 = constEnv[lis[i+1].arg_list[1].name]
                new_lis.append(virtual.Virtual_Asm("slli", 3, [asm.arg_list[0], asm.arg_list[1], virtual.Reg("2", "int")]))
                new_lis.append(virtual.Virtual_Asm(lis[i+2].instr_name, 3, [lis[i+2].arg_list[0], asm.arg_list[0], virtual.Reg(str(var1), "int")]))
                i += 3
                continue
            elif asm.arg_list[1].name in constEnv: # 2番目の引数だけ定数の場合、slli,add,lw_or_flwのうちslliはあらかじめ計算することで減らすことができる
                var2 = constEnv[asm.arg_list[1].name]
                new_lis.append(virtual.Virtual_Asm("addi", 3, [lis[i+1].arg_list[0], lis[i+1].arg_list[1], virtual.Reg(str(int(var2) * 4), "int")]))
                new_lis.append(virtual.Virtual_Asm(lis[i+2].instr_name, 3, [lis[i+2].arg_list[0], lis[i+1].arg_list[0], virtual.Reg("0", "int")]))
                i += 3
                continue
        
        # Put命令
        elif asm.instr_name == "slli" and re.match(r"put1\..*", asm.arg_list[0].name) != None:
            if asm.arg_list[1].name in constEnv and lis[i+1].arg_list[1].name in constEnv: # Put命令の2つの引数がどちらも定数だった場合、slli,add,sw_or_fswを一つのsw_or_fswにすることができる
                var1 = constEnv[lis[i+1].arg_list[1].name]
                var2 = constEnv[asm.arg_list[1].name]
                new_lis.append(virtual.Virtual_Asm(lis[i+2].instr_name + "i", 2, [lis[i+2].arg_list[1], virtual.Reg(str(int(var1) + int(var2) * 4), "int")]))
                i += 3
                continue
            elif lis[i+1].arg_list[1].name in constEnv: # 1番目の引数だけ定数の場合、slli,add,sw_or_fswのうちaddは減らすことができる
                var1 = constEnv[lis[i+1].arg_list[1].name]
                new_lis.append(virtual.Virtual_Asm("slli", 3, [asm.arg_list[0], asm.arg_list[1], virtual.Reg("2", "int")]))
                new_lis.append(virtual.Virtual_Asm(lis[i+2].instr_name, 3, [asm.arg_list[0], lis[i+2].arg_list[1], virtual.Reg(str(var1), "int")]))
                i += 3
                continue
            elif asm.arg_list[1].name in constEnv: # 2番目の引数だけ定数の場合、slli,add,sw_or_fswのうちslliはあらかじめ計算することで減らすことができる
                var2 = constEnv[asm.arg_list[1].name]
                new_lis.append(virtual.Virtual_Asm("addi", 3, [lis[i+1].arg_list[0], lis[i+1].arg_list[1], virtual.Reg(str(int(var2) * 4), "int")]))
                new_lis.append(virtual.Virtual_Asm(lis[i+2].instr_name, 3, [lis[i+1].arg_list[0], lis[i+2].arg_list[1], virtual.Reg("0", "int")]))
                i += 3
                continue
            
        new_lis.append(asm)
        i += 1

    return new_lis