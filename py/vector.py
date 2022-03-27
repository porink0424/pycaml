#--------------------------------------------------
#
# vector.py
# 4つのsw, lwを一気に行う64bit命令vsw, vlwに置換する
#
#--------------------------------------------------

import virtual
from typing import List

VECTOR_LENGTH = 4

def replace (lis:List[virtual.Virtual_Asm]) -> List[virtual.Virtual_Asm]:
    new_lis = []

    i = 0
    while i < len(lis):
        asm = lis[i]

        # 連続するlwを圧縮
        if (
            (asm.instr_name == "lw" or asm.instr_name == "flw") and
            (asm.arg_list[0].name != asm.arg_list[1].name) and
            (i+1 < len(lis)) and
            (lis[i+1].instr_name == "lw" or lis[i+1].instr_name == "flw") and
            asm.arg_list[1].name == lis[i+1].arg_list[1].name and
            abs(int(asm.arg_list[2].name) - int(lis[i+1].arg_list[2].name)) == 4
        ):
            # 連続するlwを取得
            lw_lis = [asm]
            i += 1

            # オフセットが0,4,8,12の順に並ぶ場合True, 0, -4, -8, -12の順に並ぶ場合Falseになるフラグ
            offset_asc = True

            while i < len(lis):
                # lwの次の命令もlwであり，基準レジスタと代入レジスタが同じではなく，オフセットが前の命令の+4になっていて，基準レジスタが同じ場合
                if (
                    (lis[i].instr_name == "lw" or lis[i].instr_name == "flw") and
                    (lis[i].arg_list[0].name != lis[i].arg_list[1].name) and
                    int(lis[i].arg_list[2].name) == int(lw_lis[-1].arg_list[2].name) + 4 and
                    lis[i].arg_list[1].name == lw_lis[-1].arg_list[1].name
                ):
                    lw_lis.append(lis[i])
                    i += 1

                    # lw_lisの長さがVECTOR_LENGTHを超えたときループから抜ける
                    if len(lw_lis) >= VECTOR_LENGTH:
                        break
                # lwの次の命令もlwであり，オフセットが前の命令の-4になっていて，基準レジスタが同じ場合
                elif (
                    (lis[i].instr_name == "lw" or lis[i].instr_name == "flw") and
                    (lis[i].arg_list[0].name != lis[i].arg_list[1].name) and
                    int(lis[i].arg_list[2].name) == int(lw_lis[-1].arg_list[2].name) - 4 and
                    lis[i].arg_list[1].name == lw_lis[-1].arg_list[1].name
                ):
                    offset_asc = False
                    lw_lis.append(lis[i])
                    i += 1

                    # lw_lisの長さがVECTOR_LENGTHを超えたときループから抜ける
                    if len(lw_lis) >= VECTOR_LENGTH:
                        break
                else:
                    break
            
            # 連続するlwをvlwに圧縮
            mask = [1 for _ in range(VECTOR_LENGTH)]
            if len(lw_lis) < VECTOR_LENGTH: # lw_lisが足りなければx0で補う
                res = VECTOR_LENGTH - len(lw_lis)
                lw_len = len(lw_lis)
                for j in range(res):
                    lw_lis.append(virtual.Virtual_Asm(
                        "lw",
                        3,
                        [
                            virtual.Reg("x0", "int"),
                            lw_lis[-1].arg_list[1],
                            virtual.Reg(str(int(lw_lis[-1].arg_list[2].name) + 4), "int") if offset_asc else virtual.Reg(str(int(lw_lis[-1].arg_list[2].name) - 4), "int")
                        ]))
                    mask[lw_len + j] = 0
                    
            
            if not offset_asc:
                lw_lis.reverse()
                mask.reverse()
            
            new_lis.append(virtual.Virtual_Asm("vlw", VECTOR_LENGTH + 3, [lw_lis[0].arg_list[1]] + [
                lw_asm.arg_list[0] for lw_asm in lw_lis
            ] + [lw_lis[0].arg_list[2], virtual.Reg("".join(list(map(str, mask))), "int")]))
        
        # 連続するswを圧縮
        elif (
            (asm.instr_name == "sw" or asm.instr_name == "fsw") and
            (lis[i].arg_list[0].name != lis[i].arg_list[1].name) and
            (i+1 < len(lis)) and
            (lis[i+1].instr_name == "sw" or lis[i+1].instr_name == "fsw") and
            asm.arg_list[0].name == lis[i+1].arg_list[0].name and
            abs(int(asm.arg_list[2].name) - int(lis[i+1].arg_list[2].name)) == 4
        ):
            # 連続するswを取得
            sw_lis = [asm]
            i += 1

            # オフセットが0,4,8,12の順に並ぶ場合True, 0, -4, -8, -12の順に並ぶ場合Falseになるフラグ
            offset_asc = True

            while i < len(lis):
                # swの次の命令もswであり，基準レジスタと代入レジスタが同じではなく，オフセットが前の命令の+4になっていて，基準レジスタが同じ場合
                if (
                    (lis[i].instr_name == "sw" or lis[i].instr_name == "fsw") and
                    (lis[i].arg_list[0].name != lis[i].arg_list[1].name) and
                    int(lis[i].arg_list[2].name) == int(sw_lis[-1].arg_list[2].name) + 4 and
                    lis[i].arg_list[0].name == sw_lis[-1].arg_list[0].name
                ):
                    sw_lis.append(lis[i])
                    i += 1

                    # sw_lisの長さがVECTOR_LENGTHを超えたときループから抜ける
                    if len(sw_lis) >= VECTOR_LENGTH:
                        break
                # swの次の命令もswであり，オフセットが前の命令の-4になっていて，基準レジスタが同じ場合
                elif (
                    (lis[i].instr_name == "sw" or lis[i].instr_name == "fsw") and
                    (lis[i].arg_list[0].name != lis[i].arg_list[1].name) and
                    int(lis[i].arg_list[2].name) == int(sw_lis[-1].arg_list[2].name) - 4 and
                    lis[i].arg_list[0].name == sw_lis[-1].arg_list[0].name
                ):
                    offset_asc = False
                    sw_lis.append(lis[i])
                    i += 1

                    # sw_lisの長さがVECTOR_LENGTHを超えたときループから抜ける
                    if len(sw_lis) >= VECTOR_LENGTH:
                        break
                else:
                    break
            
            # 連続するswをvswに圧縮
            mask = [1 for _ in range(VECTOR_LENGTH)]
            if len(sw_lis) < VECTOR_LENGTH: # sw_lisが足りなければx0で補う
                res = VECTOR_LENGTH - len(sw_lis)
                sw_len = len(sw_lis)
                for j in range(res):
                    sw_lis.append(virtual.Virtual_Asm(
                        "sw",
                        3,
                        [
                            sw_lis[-1].arg_list[0],
                            virtual.Reg("x0", "int"),
                            virtual.Reg(str(int(sw_lis[-1].arg_list[2].name) + 4), "int") if offset_asc else virtual.Reg(str(int(sw_lis[-1].arg_list[2].name) - 4), "int")
                        ]))
                    mask[sw_len + j] = 0
                    
            
            if not offset_asc:
                sw_lis.reverse()
                mask.reverse()
            
            new_lis.append(virtual.Virtual_Asm("vsw", VECTOR_LENGTH + 3, [sw_lis[0].arg_list[0]] + [
                sw_asm.arg_list[1] for sw_asm in sw_lis
            ] + [sw_lis[0].arg_list[2], virtual.Reg("".join(list(map(str, mask))), "int")]))

        else:
            new_lis.append(asm)
            i += 1

    
    return new_lis
            

def leftAlign (lis:List[virtual.Virtual_Asm]) -> List[virtual.Virtual_Asm]:
    i = 0
    while i < len(lis):
        if lis[i].instr_name == "vsw" or lis[i].instr_name == "vlw":
            if lis[i].arg_list[6].name == "0011":
                lis[i].arg_list[1] = virtual.Reg(lis[i].arg_list[3].name, lis[i].arg_list[3].typ)
                lis[i].arg_list[2] = virtual.Reg(lis[i].arg_list[4].name, lis[i].arg_list[4].typ)
                lis[i].arg_list[3] = virtual.Reg("x0", "int")
                lis[i].arg_list[4] = virtual.Reg("x0", "int")
                lis[i].arg_list[6].name = "1100"
                lis[i].arg_list[5].name = str(int(lis[i].arg_list[5].name) + 8)
            elif lis[i].arg_list[6].name == "0111":
                lis[i].arg_list[1] = virtual.Reg(lis[i].arg_list[2].name, lis[i].arg_list[2].typ)
                lis[i].arg_list[2] = virtual.Reg(lis[i].arg_list[3].name, lis[i].arg_list[3].typ)
                lis[i].arg_list[3] = virtual.Reg(lis[i].arg_list[4].name, lis[i].arg_list[4].typ)
                lis[i].arg_list[4] = virtual.Reg("x0", "int")
                lis[i].arg_list[6].name = "1110"
                lis[i].arg_list[5].name = str(int(lis[i].arg_list[5].name) + 4)
        i += 1
    
    return lis