#--------------------------------------------------
#
# tail.py
# 末尾呼び出し最適化をかける
#
#--------------------------------------------------

from typing import List
import virtual

# 末尾かどうかを判定する
def isTail (instr_idx:int, lis:List[virtual.Virtual_Asm]) -> bool:
    try:
        next_instr_idx = instr_idx + 1
        while True:
            # 次の命令がjであれば、そのジャンプ先をみに行く
            if lis[next_instr_idx].instr_name == "j":
                j_label = lis[next_instr_idx].arg_list[0].name # ジャンプ先のアドレスを取得
                while next_instr_idx < len(lis) and lis[next_instr_idx].instr_name != j_label + ":": # ジャンプ先のアドレスに辿り着くまでスキップ
                    next_instr_idx += 1

            # 次の命令がラベルや意味のない命令であれば、その次をみに行く
            elif ":" in lis[next_instr_idx].instr_name or lis[next_instr_idx].instr_name == "nop": 
                next_instr_idx += 1
            else:
                break
        
        # 辿り着いた先がretやret_unitであれば末尾である
        if lis[next_instr_idx].instr_name in {"ret", "ret_unit"}:
            return True
        else: # それ以外は末尾ではない
            return False
    except IndexError:
        return False

# メイン部分
def tailCallOpt (lis:List[virtual.Virtual_Asm]) -> List[virtual.Virtual_Asm]:
    new_lis = []
    for i in range(len(lis)):
        if lis[i].instr_name in {
            "just_call_dir",
            "just_call_cls",
            "recv_ret_val_dir_int",
            "recv_ret_val_dir_float",
            "recv_ret_val_cls_int",
            "recv_ret_val_cls_float"
        } and isTail(i, lis):
            if "recv_ret_val_dir" in lis[i].instr_name:
                new_lis.append(virtual.Virtual_Asm("just_call_dir_and_jump", lis[i].arg_count - 1, lis[i].arg_list[1:]))
            elif "recv_ret_val_cls" in lis[i].instr_name:
                new_lis.append(virtual.Virtual_Asm("just_call_cls_and_jump", lis[i].arg_count - 1, lis[i].arg_list[1:]))
            elif lis[i].instr_name == "just_call_dir":
                new_lis.append(virtual.Virtual_Asm("just_call_dir_and_jump", lis[i].arg_count, lis[i].arg_list))
            elif lis[i].instr_name == "just_call_cls":
                new_lis.append(virtual.Virtual_Asm("just_call_cls_and_jump", lis[i].arg_count, lis[i].arg_list))
        else:
            new_lis.append(lis[i])
    return new_lis
