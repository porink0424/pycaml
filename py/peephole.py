#--------------------------------------------------
#
# peephole.py
# のぞき穴最適化をかける
#
#--------------------------------------------------

from typing import List
import virtual

def peepholeOpt (lis:List[virtual.Virtual_Asm]) -> List[virtual.Virtual_Asm]:
    for j in range(len(lis)):
        virtual_asm = lis[j]
        if virtual_asm.instr_name == "mv" or virtual_asm.instr_name == "fmv":
            if virtual_asm.arg_list[0].name == virtual_asm.arg_list[1].name: # 同一レジスタへの不要なmoveを削除
                lis[j] = virtual.Virtual_Asm("nop", 0, [])
            elif j + 1 < len(lis) and (lis[j+1].instr_name == "mv" or lis[j+1].instr_name == "fmv") and (lis[j].arg_list[0].name == lis[j+1].arg_list[1].name and lis[j].arg_list[1].name == lis[j+1].arg_list[0].name): # 2つのレジスタを不要にmoveし合うのを片方削除
                lis[j+1] = virtual.Virtual_Asm("nop", 0, [])

        # addi a1, a3, 16
        # fsw fa0, 0(a1)
        # のような命令を
        # addi a1, a3, 16
        # fsw fa0, 16(a3)
        # のように置き換えることで最適化（addiが消えることも望める）
        elif virtual_asm.instr_name == "addi" and virtual_asm.arg_list[0].name != "sp" and virtual_asm.arg_list[1].name != "sp":
            if j+1 < len(lis) and (lis[j+1].instr_name == "sw" or lis[j+1].instr_name == "fsw"):
                if lis[j+1].arg_list[0].name == virtual_asm.arg_list[0].name:
                    lis[j+1].arg_list[0] = virtual_asm.arg_list[1]
                    lis[j+1].arg_list[2] = virtual.Reg(str(int(lis[j+1].arg_list[2].name)+int(virtual_asm.arg_list[2].name)), "int")
            elif j+1 < len(lis) and (lis[j+1].instr_name == "lw" or lis[j+1].instr_name == "flw"):
                if lis[j+1].arg_list[1].name == virtual_asm.arg_list[0].name:
                    lis[j+1].arg_list[1] = virtual_asm.arg_list[1]
                    lis[j+1].arg_list[2] = virtual.Reg(str(int(lis[j+1].arg_list[2].name)+int(virtual_asm.arg_list[2].name)), "int")
            
    # 無意味なaddi命令の削除
    # addi a1, a1, 0
    # など
    new_lis = []
    for j in range(len(lis)):
        asm = lis[j]
        if asm.instr_name == "addi" and asm.arg_list[0].name == asm.arg_list[1].name and asm.arg_list[2].name == str(0):
            continue
        else:
            new_lis.append(asm)

    return new_lis
