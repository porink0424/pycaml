#--------------------------------------------------
#
# inline.py
# インライン最適化をかける
#
#--------------------------------------------------

from typing import List
import virtual

# 特定の組み込み関数に関して、呼び出しのインライン化を施す
def inlineOpt (lis:List[virtual.Virtual_Asm]) -> virtual.Virtual_Asm:
    new_lis = []
    for asm in lis:
        if asm.instr_name == "recv_ret_val_dir_float":
            if asm.arg_list[1].name == "min_caml_float_of_int":
                new_lis.append(virtual.Virtual_Asm("fcvt.s.w", 2, [asm.arg_list[0], asm.arg_list[2]]))
                continue
            elif asm.arg_list[1].name == "min_caml_fneg":
                new_lis.append(virtual.Virtual_Asm("fneg", 2, [asm.arg_list[0], asm.arg_list[2]]))
                continue
            elif asm.arg_list[1].name == "min_caml_fsqr":
                new_lis.append(virtual.Virtual_Asm("fmul", 2, [asm.arg_list[0], asm.arg_list[2], asm.arg_list[2]]))
                continue
            elif asm.arg_list[1].name == "min_caml_fabs":
                new_lis.append(virtual.Virtual_Asm("fabs", 2, [asm.arg_list[0], asm.arg_list[2]]))
                continue
            elif asm.arg_list[1].name == "min_caml_sqrt":
                new_lis.append(virtual.Virtual_Asm("fsqrt", 2, [asm.arg_list[0], asm.arg_list[2]]))
                continue
        elif asm.instr_name == "recv_ret_val_dir_int":
            if asm.arg_list[1].name == "min_caml_int_of_float":
                new_lis.append(virtual.Virtual_Asm("fcvt.w.s", 2, [asm.arg_list[0], asm.arg_list[2]]))
                continue
            elif asm.arg_list[1].name == "min_caml_fless":
                new_lis.append(virtual.Virtual_Asm("flt", 3, [asm.arg_list[0], asm.arg_list[3], asm.arg_list[2]]))
                continue
            elif asm.arg_list[1].name == "min_caml_fisneg":
                new_lis.append(virtual.Virtual_Asm("fmv.w.x", 3, [virtual.Reg("f4", "float"), virtual.Reg("x0", "int")]))
                new_lis.append(virtual.Virtual_Asm("flt", 3, [asm.arg_list[0], asm.arg_list[2], virtual.Reg("f4", "float")]))
                continue
            elif asm.arg_list[1].name == "min_caml_fispos":
                new_lis.append(virtual.Virtual_Asm("fmv.w.x", 3, [virtual.Reg("f4", "float"), virtual.Reg("x0", "int")]))
                new_lis.append(virtual.Virtual_Asm("flt", 3, [asm.arg_list[0], virtual.Reg("f4", "float"), asm.arg_list[2]]))
                continue
            elif asm.arg_list[1].name == "min_caml_fiszero":
                new_lis.append(virtual.Virtual_Asm("fmv.w.x", 3, [virtual.Reg("f4", "float"), virtual.Reg("x0", "int")]))
                new_lis.append(virtual.Virtual_Asm("feq", 3, [asm.arg_list[0], virtual.Reg("f4", "float"), asm.arg_list[2]]))
                continue
        new_lis.append(asm)
    
    return new_lis
                