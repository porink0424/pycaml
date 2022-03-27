#--------------------------------------------------
#
# emit.py
# 最終的なアセンブリを、比較的簡単な最適化を数回かけてから出力する
#
#--------------------------------------------------

from typing import List
import virtual
import peephole
import spOpt
import jumpOpt
import lwStallOpt
import vector

# 比較的簡単な最適化を繰り返す回数
OPT_LOOP_CNT = 10

# nop命令の削除
def deleteNop (lis:List[virtual.Virtual_Asm]) -> List[virtual.Virtual_Asm]:
    new_lis = []
    for asm in lis:
        if asm.instr_name != "nop":
            new_lis.append(asm)
    return new_lis

# メイン部分
def VirtualAsmList2Str (lis:List[virtual.Virtual_Asm]) -> str:
    # ここまで実行したきた関数の中で最後に処理するべきものとして残されていたものを処理する
    for j in range(len(lis)):
        virtual_asm = lis[j]
        # virtualにおける「自己再帰で使われる場合があるのでラベルを保持しておく」に対する処理
        for i in range(len(virtual_asm.arg_list)):
            if "cls_address" in virtual_asm.arg_list[i].name:
                virtual_asm.arg_list[i] = virtual.Reg("a0", "int")
        # negという命令はないので置き換える
        if virtual_asm.instr_name == "neg":
            lis[j] = virtual.Virtual_Asm("sub", 3, [virtual_asm.arg_list[0], virtual.Reg("x0", "int"), virtual_asm.arg_list[1]])
        # regAllocにおける「不要定義削除」に対する処理
        if len(virtual_asm.arg_list) > 0 and virtual_asm.arg_list[0].name == "unnecessary":
            lis[j] = virtual.Virtual_Asm("nop", 0, [])
        # swi, fswi, lwi, flwiの置き換え
        if virtual_asm.instr_name == "swi" or virtual_asm.instr_name == "fswi":
            lis[j] = virtual.Virtual_Asm(virtual_asm.instr_name.replace('i', ''), 3, [virtual.Reg("x0", "int"), virtual_asm.arg_list[0], virtual_asm.arg_list[1]])
        if virtual_asm.instr_name == "lwi" or virtual_asm.instr_name == "flwi":
            lis[j] = virtual.Virtual_Asm(virtual_asm.instr_name.replace('i', ''), 3, [virtual_asm.arg_list[0], virtual.Reg("x0", "int"), virtual_asm.arg_list[1]])

    # 最適化をループ
    for _ in range(OPT_LOOP_CNT):
        lis = peephole.peepholeOpt(lis) # 覗き穴最適化
        lis = spOpt.spOpt(lis, 0) # spのaddi命令の最適化
        lis = jumpOpt.jumpOpt(lis) # 連続するjump命令の最適化
        lis = vector.replace(lis) # 連続するlw, swの最適化
        lis = vector.leftAlign(lis)
        lis = deleteNop(lis)
    
    # branchの後に連続するjump命令の最適化
    lis = jumpOpt.branchOpt(lis)

    # # lwに連続する命令がストールする問題への対処を行う最適化
    lis = lwStallOpt.lwStallOpt(lis)

    # 文字列化
    ret = ""
    for virtual_asm in lis:
        if ":" in virtual_asm.instr_name: # labelの中にドットが入っているとまずいのでアンダースコアに変える
            ret += virtual_asm.instr_name.replace(".", "_")
        elif "#" in virtual_asm.instr_name: # comment
            ret += virtual_asm.instr_name
        elif virtual_asm.instr_name == "fli": # fli命令の第二引数はドットをアンダースコアに変える必要はない
            ret += "\t" + (virtual_asm.instr_name + "          ")[:10] + virtual_asm.arg_list[0].name.replace(".", "_") + ", " + virtual_asm.arg_list[1].name
        elif virtual_asm.instr_name == "sw" or virtual_asm.instr_name == "fsw": # storeの命令の形を整える
            ret += "\t" + (virtual_asm.instr_name + "          ")[:10] + virtual_asm.arg_list[1].name.replace(".", "_") + ", " + virtual_asm.arg_list[2].name + "(" + virtual_asm.arg_list[0].name.replace(".", "_") + ")"
        elif virtual_asm.instr_name == "lw" or virtual_asm.instr_name == "flw": # loadの命令の形を整える
            ret += "\t" + (virtual_asm.instr_name + "          ")[:10] + virtual_asm.arg_list[0].name.replace(".", "_") + ", " + virtual_asm.arg_list[2].name + "(" + virtual_asm.arg_list[1].name.replace(".", "_") + ")"
        elif virtual_asm.instr_name == "vlw": # vector load命令の形を整える
            ret += "\t" + (virtual_asm.instr_name + "          ")[:10] + virtual_asm.arg_list[1].name.replace(".", "_") + ", " + virtual_asm.arg_list[2].name.replace(".", "_") + ", " + virtual_asm.arg_list[3].name.replace(".", "_") + ", " + virtual_asm.arg_list[4].name.replace(".", "_") + ", " + virtual_asm.arg_list[5].name + "(" + virtual_asm.arg_list[0].name.replace(".", "_") + "), " + virtual_asm.arg_list[6].name
        elif virtual_asm.instr_name == "vsw": # vector store命令の形を整える
            ret += "\t" + (virtual_asm.instr_name + "          ")[:10] + virtual_asm.arg_list[1].name.replace(".", "_") + ", " + virtual_asm.arg_list[2].name.replace(".", "_") + ", " + virtual_asm.arg_list[3].name.replace(".", "_") + ", " + virtual_asm.arg_list[4].name.replace(".", "_") + ", " + virtual_asm.arg_list[5].name + "(" + virtual_asm.arg_list[0].name.replace(".", "_") + "), " + virtual_asm.arg_list[6].name
        elif virtual_asm.instr_name == "jalr" and virtual_asm.arg_count == 3: # jalrの命令の形を整える
            ret += "\t" + (virtual_asm.instr_name + "          ")[:10] + virtual_asm.arg_list[0].name.replace(".", "_") + ", " + virtual_asm.arg_list[2].name + "(" + virtual_asm.arg_list[1].name.replace(".", "_") + ")"
        else:
            ret += "\t" + (virtual_asm.instr_name + "          ")[:10] + ", ".join([reg.name.replace(".", "_") for reg in virtual_asm.arg_list])
        ret += "\n"
    return ret
