#--------------------------------------------------
#
# spOpt.py
# スタックポインタのaddi命令をできるだけまとめて計算する
# 計算を保留していて、lw, swなどの命令を呼び出す際は、オフセットを調整することで対応
#
#--------------------------------------------------

from typing import List
import virtual

def spOpt (lis:List[virtual.Virtual_Asm], height_dif:int) -> List[virtual.Virtual_Asm]:
    new_lis = []
    i = 0
    while i < len(lis):
        asm = lis[i]
        if asm.instr_name == "beq" or asm.instr_name == "bge" or asm.instr_name == "blt" or asm.instr_name == "bfeq" or asm.instr_name == "bfle" or asm.instr_name == "bflt":
            new_lis.append(asm)
            i += 1
            num = asm.arg_list[2].name.replace("then", "") # thenの後についている数字の取得
            # else節部分のアセンブリを取得
            else_lis = []
            while "then" + str(num) + ":" != lis[i].instr_name:
                else_lis.append(lis[i])
                i += 1
            # then節部分のアセンブリを取得
            then_lis = []
            while "endif" + str(num) + ":" != lis[i].instr_name:
                then_lis.append(lis[i])
                i += 1
            
            else_lis = spOpt(else_lis, height_dif)
            then_lis = spOpt(then_lis, height_dif)

            new_lis += else_lis + then_lis
            height_dif = 0
        
        elif asm.instr_name == "addi":
            if asm.arg_list[0].name == "sp" and asm.arg_list[1].name == "sp":
                height_dif += int(asm.arg_list[2].name)
            else:
                new_lis.append(asm)
            i += 1

        elif asm.instr_name == "lw" or asm.instr_name == "flw":
            if asm.arg_list[1].name == "sp":
                new_lis.append(virtual.Virtual_Asm(asm.instr_name, asm.arg_count, [asm.arg_list[0], asm.arg_list[1], virtual.Reg(str(int(asm.arg_list[2].name) + height_dif), "int")]))
            else:
                new_lis.append(asm)
            i += 1

        elif asm.instr_name == "sw" or asm.instr_name == "fsw":
            if asm.arg_list[0].name == "sp":
                new_lis.append(virtual.Virtual_Asm(asm.instr_name, asm.arg_count, [asm.arg_list[0], asm.arg_list[1], virtual.Reg(str(int(asm.arg_list[2].name) + height_dif), "int")]))
            else:
                new_lis.append(asm)
            i += 1
        
        elif asm.instr_name == "vlw" or asm.instr_name == "vsw":
            if asm.arg_list[0].name == "sp":
                new_lis.append(virtual.Virtual_Asm(asm.instr_name, asm.arg_count, [asm.arg_list[0], asm.arg_list[1], asm.arg_list[2], asm.arg_list[3], asm.arg_list[4], virtual.Reg(str(int(asm.arg_list[5].name) + height_dif), "int"), asm.arg_list[6]]))
            else:
                new_lis.append(asm)
            i += 1

        # 今までheight_difで調整してきたが、関数の呼び出し直前では、spを実際に変更する必要がある
        elif asm.instr_name == "call" or asm.instr_name == "jalr":
            if height_dif != 0:
                new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(height_dif), "int")]))
                height_dif = 0
            new_lis.append(asm)
            i += 1
        else:
            new_lis.append(asm)
            i += 1


    # 関数が返るときは、spの計算をする（基本的にはnew_lisの最後に入れればよく、j,ret,jalrがあるときは一個前に入れる）
    if height_dif != 0:
        if new_lis[-1].instr_name in {"ret", "j", "jalr"}:
            if len(new_lis) >= 2 and new_lis[-2].instr_name in {"ret", "j", "jalr"}:
                new_lis.insert(-2, virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(height_dif), "int")]))
            else:
                new_lis.insert(-1, virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(height_dif), "int")]))
        else:
            new_lis.append(virtual.Virtual_Asm("addi", 3, [virtual.Reg("sp", "int"), virtual.Reg("sp", "int"), virtual.Reg(str(height_dif), "int")]))

    return new_lis
