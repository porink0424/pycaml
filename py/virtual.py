#--------------------------------------------------
#
# virtual.py
# Closure_tから、（レジスタ割り当てをしていない）仮想的なアセンブリのリストに変換する
#
# 実装の方針：
# closure_tが与えられるので、それを仮想的な命令列に落とし込んでいくことを考える。例えば
# Add(Var(x), Var(y))
# というものに対して、これをアセンブリに落とし込もうとすると
# add {} x, y
# の形になる。ただ、{}の部分には何が入るかはAdd(Var(x), Var(y))単体だけをみても何もわからない。これはLet()等によって
# Let((var,t), Add(Var(x), Var(y)))
# という形になることで初めて
# add var, x, y
# とすればよいのだとわかる。すなわち、{}の部分は一旦放置し（このプログラム内ではこれを"!"と表している）、Letの処理のときに{}の部分を置き換える、という方針で計算を進めていけば良い。
#
#--------------------------------------------------

from typing import List, Tuple
from struct import *
import closure
import reglist
import error

# 仮想レジスタの型
# int: 整数
# float: 小数
# (): unit型
# label: ラベル
# これら4種類のどれかに統一（todo: 本当にできているか確認）
class Reg:
    def __init__ (self, name:str, typ:str):
        self.name = name
        self.typ = typ

# 仮想アセンブリの型
class Virtual_Asm:
    def __init__ (self, instr_name:str, arg_count:int, arg_list:List[Reg]):
        self.instr_name = instr_name
        self.arg_count = arg_count
        self.arg_list = arg_list

# 変数の名前から変数の型への写像
class Env:
    def __init__ (self):
        self.env = {}
    def get (self, arg_name:str) -> str:
        if arg_name in self.env:
            return self.env[arg_name]
        elif arg_name in reglist.SPECIAL_INT_REGS: # 特別な用途の整数レジスタの名前が来た場合は、envに入っていなくてもintとわかる
            return "int"
        elif arg_name in reglist.SPECIAL_FLOAT_REGS: # 特別な用途の小数レジスタの名前が来た場合は、envに入っていなくてもfloatとわかる
            return "float"
        else: # 型が登録されていないレジスタ
            error.error("Warning: {} is not added to env.".format(arg_name))
    def set (self, arg_name:str, typ:str):
        self.env[arg_name] = typ

# 変数名を一意にするために、以下の変数をカウンターとして利用する
flt_cnt = 0
if_cnt = 0
tuple_cnt = 0
get_cnt = 0
put_cnt = 0
fundef_cnt = 0
appcls_cnt = 0
appdir_cnt = 0
makecls_cnt = 0

# Envオブジェクトの作成
env = Env()

# arg_listをintのリストとfloatのリストに分割する
def separateIntAndFloat (args_list:List[str]) -> Tuple[List[str], List[str]]:
    int_list = []
    float_list = []
    for arg in args_list:
        typ = env.get(arg)
        if typ == "float":
            float_list.append(arg)
        elif typ == "()":
            continue
        else:
            int_list.append(arg)
    return int_list, float_list

# 仮想命令のリストlisのうち、変数の名前が!になっているところを引数newで置き換える処理
def replaceAllExcl (lis:List[Virtual_Asm], new:Reg) -> List[Virtual_Asm]:
    for virtual_asm in lis:
        # Getに対する処理
        if virtual_asm.instr_name == "lw_or_flw":
            if new.typ == "float": # 置き換えたい変数newの型はfloatなので、flwを使う
                virtual_asm.instr_name = "flw"
                virtual_asm.arg_list[0] = new
            else: # 置き換えたい変数newの型はfloat以外なので、lwを使う
                virtual_asm.instr_name = "lw"
                virtual_asm.arg_list[0] = Reg(new.name, "int")

        # Appclsの返り値に対する処理
        elif virtual_asm.instr_name == "app_cls":
            if new.typ == "float":
                virtual_asm.instr_name = "recv_ret_val_cls_float"
                virtual_asm.arg_list[0] = new
            elif new.typ == "()": # 置き換えたい変数の型はUnit、つまり返り値を格納する必要がない
                virtual_asm.instr_name = "just_call_cls"
                virtual_asm.arg_list.pop(0)
                virtual_asm.arg_count -= 1
            else:
                virtual_asm.instr_name = "recv_ret_val_cls_int"
                virtual_asm.arg_list[0] = Reg(new.name, "int")
        
        # Appdirの返り値に対する処理
        elif virtual_asm.instr_name == "app_dir": 
            if new.typ == "float":
                virtual_asm.instr_name = "recv_ret_val_dir_float"
                virtual_asm.arg_list[0] = new
            elif new.typ == "()":
                virtual_asm.instr_name = "just_call_dir"
                virtual_asm.arg_list.pop(0)
                virtual_asm.arg_count -= 1
            else:
                virtual_asm.instr_name = "recv_ret_val_dir_int"
                virtual_asm.arg_list[0] = Reg(new.name, "int")
        
        # その他の命令に対する処理
        else:
            for i in range(len(virtual_asm.arg_list)):
                if virtual_asm.arg_list[i].name == "!": # !があればそこをnewで置き換える
                    typ = "float" if virtual_asm.arg_list[i].typ == "float" else "int"
                    virtual_asm.arg_list[i] = Reg(new.name, typ)
                    env.set(new.name, typ)
    return lis

# 関数の型は、Fun([引数の型], 返り値の型)という構造になっているので、返り値の型の部分を取り出す
def retrieveRetType (fun_type:str) -> str:
    fun_type = fun_type[4:-1] # Fun()を取り出す
    cnt = 0
    for i in range(len(fun_type)):
        if fun_type[i] == "[":
            cnt += 1
        if fun_type[i] == "]":
            cnt -= 1
            if cnt == 0:
                break
    if fun_type[i+2:] == "float":
        ret_type = "float"
    elif fun_type[i+2:] == "()":
        ret_type = "()"
    else:
        ret_type = "int"
    return ret_type

# メイン部分のClosure_t2VirtualAsm_loopで計算した結果、!が残ってゴミになっている部分を消去する
# このようなゴミが残る現象は、例えば単に "Let((Ti1.2,int),Int(3),AppDir(min_caml_debug_int,[Ti1.2,]))" 等を実行したときに起こる。
def Closure_t2VirtualAsm (closure_t:closure.Closure_t, fundefs:List[closure.Fundef]) -> List[Virtual_Asm]:
    lis = Closure_t2VirtualAsm_loop(closure_t, fundefs)
    for i in range(len(lis)):
        virtual_asm = lis[i]
        if (virtual_asm.instr_name == "mv") and virtual_asm.arg_list[0].name == "!": # mvの受け取る先がなければ，無視
            lis[i] = Virtual_Asm("nop", 0, [])
        elif ("app_dir" in virtual_asm.instr_name) and virtual_asm.arg_list[0].name == "!": # app_dirの受け取る先がなければ，関数を呼ぶだけにする
            virtual_asm.instr_name = "just_call_dir"
            virtual_asm.arg_count -= 1
            virtual_asm.arg_list.pop(0)
        elif ("app_cls" in virtual_asm.instr_name) and virtual_asm.arg_list[0].name == "!": # app_clsの受け取る先がなければ，関数を呼ぶだけにする
            virtual_asm.instr_name = "just_call_cls"
            virtual_asm.arg_count -= 1
            virtual_asm.arg_list.pop(0)
    return lis

# メイン部分
def Closure_t2VirtualAsm_loop (closure_t:closure.Closure_t, fundefs:List[closure.Fundef]) -> List[Virtual_Asm]:
    global flt_cnt, if_cnt, tuple_cnt, get_cnt, put_cnt, fundef_cnt, appcls_cnt, appdir_cnt, makecls_cnt, env
    typ = type(closure_t)

    if typ is closure.Unit:
        return [Virtual_Asm("nop", 0, [])]

    elif typ is closure.Int:
        return [Virtual_Asm("li", 2, [Reg("!", "int"), Reg(str(closure_t.val), "int")])]

    elif typ is closure.Float:
        flt_cnt += 1
        if closure_t.val == 0.0: # ゼロレジスタを使って初期化すればよい
            return [
                Virtual_Asm("fmv.w.x", 2, [Reg("!", "float"), Reg("x0", "int")]),
            ]
        else:
            return [
                Virtual_Asm("fli", 2, [Reg("!", "float"), Reg(str(closure_t.val), "float")])
            ]

    elif typ is closure.Neg:
        return [Virtual_Asm("neg", 2, [Reg("!", "int"), Reg(str(closure_t.var), "int")])]

    elif typ is closure.Add:
        return [Virtual_Asm("add", 3, [Reg("!", "int"), Reg(str(closure_t.var1), "int"), Reg(str(closure_t.var2), "int")])]
    elif typ is closure.Sub:
        return [Virtual_Asm("sub", 3, [Reg("!", "int"), Reg(str(closure_t.var1), "int"), Reg(str(closure_t.var2), "int")])]
    elif typ is closure.Mul:
        return [Virtual_Asm("sll", 3, [Reg("!", "int"), Reg(str(closure_t.var1), "int"), Reg(str(closure_t.var2), "int")])]
    elif typ is closure.Div:
        return [Virtual_Asm("srl", 3, [Reg("!", "int"), Reg(str(closure_t.var1), "int"), Reg(str(closure_t.var2), "int")])]

    elif typ is closure.FNeg:
        return [Virtual_Asm("fneg", 2, [Reg("!", "float"), Reg(str(closure_t.var), "float")])]
    elif typ is closure.FAdd:
        return [Virtual_Asm("fadd", 3, [Reg("!", "float"), Reg(str(closure_t.var1), "float"), Reg(str(closure_t.var2), "float")])]
    elif typ is closure.FSub:
        return [Virtual_Asm("fsub", 3, [Reg("!", "float"), Reg(str(closure_t.var1), "float"), Reg(str(closure_t.var2), "float")])]
    elif typ is closure.FMul:
        return [Virtual_Asm("fmul", 3, [Reg("!", "float"), Reg(str(closure_t.var1), "float"), Reg(str(closure_t.var2), "float")])]
    elif typ is closure.FDiv:
        return [Virtual_Asm("fdiv", 3, [Reg("!", "float"), Reg(str(closure_t.var1), "float"), Reg(str(closure_t.var2), "float")])]
    
    elif typ is closure.IfEq:
        if_cnt += 1
        # ラベルとしてthenとendifのラベルを作成
        then_label = "then" + str(if_cnt)
        endif_label = "endif" + str(if_cnt)
        var1_typ = env.get(closure_t.var1) # = var2_typ
        if var1_typ == "float": # 小数同士の比較の場合
            first_asm = [
                Virtual_Asm("bfeq", 3, [Reg(str(closure_t.var1), "float"), Reg(str(closure_t.var2), "float"), Reg(then_label, "label")]),
            ]
        else: # 整数同士の比較の場合
            first_asm = [
                Virtual_Asm("beq", 3, [Reg(str(closure_t.var1), "int"), Reg(str(closure_t.var2), "int"), Reg(then_label, "label")]),
            ]
        # first_asm : branch命令
        # Closure_t2VirtualAsm_loop(closure_t.e2, fundefs) : else節の命令
        # Closure_t2VirtualAsm_loop(closure_t.e1, fundefs) : then節の命令
        return first_asm + Closure_t2VirtualAsm_loop(closure_t.e2, fundefs) + [
            Virtual_Asm("j", 1, [Reg(endif_label, "label")]),
            Virtual_Asm(then_label + ":", 0, []),
        ] + Closure_t2VirtualAsm_loop(closure_t.e1, fundefs) + [
            Virtual_Asm(endif_label + ":", 0, []),
        ]
    
    elif typ is closure.IfNEq:
        if_cnt += 1
        # ラベルとしてthenとendifのラベルを作成
        then_label = "then" + str(if_cnt)
        endif_label = "endif" + str(if_cnt)
        var1_typ = env.get(closure_t.var1) # = var2_typ
        if var1_typ == "float": # 小数同士の比較の場合
            first_asm = [
                Virtual_Asm("bfeq", 3, [Reg(str(closure_t.var1), "float"), Reg(str(closure_t.var2), "float"), Reg(then_label, "label")]),
            ]
        else: # 整数同士の比較の場合
            first_asm = [
                Virtual_Asm("beq", 3, [Reg(str(closure_t.var1), "int"), Reg(str(closure_t.var2), "int"), Reg(then_label, "label")]),
            ]
        # first_asm : branch命令
        # Closure_t2VirtualAsm_loop(closure_t.e2, fundefs) : else節の命令
        # Closure_t2VirtualAsm_loop(closure_t.e1, fundefs) : then節の命令
        # IfNEqではe1とe2をIfEqのときと逆にする
        return first_asm + Closure_t2VirtualAsm_loop(closure_t.e1, fundefs) + [
            Virtual_Asm("j", 1, [Reg(endif_label, "label")]),
            Virtual_Asm(then_label + ":", 0, []),
        ] + Closure_t2VirtualAsm_loop(closure_t.e2, fundefs) + [
            Virtual_Asm(endif_label + ":", 0, []),
        ]
    
    elif typ is closure.IfLE:
        if_cnt += 1
        then_label = "then" + str(if_cnt)
        endif_label = "endif" + str(if_cnt)
        var1_typ = env.get(closure_t.var1)
        if var1_typ == "float":
            first_asm = [
                Virtual_Asm("bfle", 3, [Reg(str(closure_t.var1), "float"), Reg(str(closure_t.var2), "float"), Reg(then_label, "label")]),
            ]
        else:
            first_asm = [
                Virtual_Asm("bge", 3, [Reg(str(closure_t.var2), "int"), Reg(str(closure_t.var1), "int"), Reg(then_label, "label")]),
            ]
        return first_asm + Closure_t2VirtualAsm_loop(closure_t.e2, fundefs) + [
            Virtual_Asm("j", 1, [Reg(endif_label, "label")]),
            Virtual_Asm(then_label + ":", 0, []),
        ] + Closure_t2VirtualAsm_loop(closure_t.e1, fundefs) + [
            Virtual_Asm(endif_label + ":", 0, []),
        ]

    elif typ is closure.IfLT:
        if_cnt += 1
        then_label = "then" + str(if_cnt)
        endif_label = "endif" + str(if_cnt)
        var1_typ = env.get(closure_t.var1)
        if var1_typ == "float":
            first_asm = [
                Virtual_Asm("bflt", 3, [Reg(str(closure_t.var1), "float"), Reg(str(closure_t.var2), "float"), Reg(then_label, "label")]),
            ]
        else:
            first_asm = [
                Virtual_Asm("blt", 3, [Reg(str(closure_t.var1), "int"), Reg(str(closure_t.var2), "int"), Reg(then_label, "label")]),
            ]
        return first_asm + Closure_t2VirtualAsm_loop(closure_t.e2, fundefs) + [
            Virtual_Asm("j", 1, [Reg(endif_label, "label")]),
            Virtual_Asm(then_label + ":", 0, []),
        ] + Closure_t2VirtualAsm_loop(closure_t.e1, fundefs) + [
            Virtual_Asm(endif_label + ":", 0, []),
        ]
    
    # replaceAllExclにより!を置換する
    elif typ is closure.Let:
        e1_asm = replaceAllExcl(Closure_t2VirtualAsm_loop(closure_t.e1, fundefs), Reg(closure_t.var, closure_t.type))
        env.set(closure_t.var, closure_t.type)
        return e1_asm + Closure_t2VirtualAsm_loop(closure_t.e2, fundefs) 
    
    # 変数の型によってmvとfmvを使い分ける
    elif typ is closure.Var:
        var_typ = env.get(closure_t.var)
        if var_typ == "float":
            return [Virtual_Asm("fmv", 2, [Reg("!", "float"), Reg(closure_t.var, "float")])]
        else:
            return [Virtual_Asm("mv", 2, [Reg("!", "int"), Reg(closure_t.var, "int")])]
    
    # クロージャ生成
    elif typ is closure.MakeCls:
        makecls_cnt += 1
        fv_length = len(closure_t.closure.actual_fv)
        # 関数のアドレスを入れる
        put_asm = [
            Virtual_Asm("la", 2, [Reg("makecls" + str(makecls_cnt), "int"), Reg(closure_t.closure.entry, "label")]),
            Virtual_Asm("sw", 3, [Reg(closure_t.var, "int"), Reg("makecls" + str(makecls_cnt), "int"), Reg("0", "int")])
        ]
        # closureに実際にデータを入れる
        int_list, float_list = separateIntAndFloat(closure_t.closure.actual_fv)
        idx = 0
        for int_arg in int_list:
            put_asm.append(Virtual_Asm("sw", 3, [Reg(closure_t.var, "int"), Reg(int_arg, "int"), Reg(str(4 * (idx+1)), "int")]))
            idx += 1
        for float_arg in float_list:
            put_asm.append(Virtual_Asm("fsw", 3, [Reg(closure_t.var, "int"), Reg(float_arg, "float"), Reg(str(4 * (idx+1)), "int")]))
            idx += 1
        # 型環境への追加
        env.set(closure_t.var, "int")
        # put_asm: 関数のアドレスと自由変数をヒープ上に入れる命令列
        return [
            Virtual_Asm("mv", 2, [Reg(closure_t.var, "int"), Reg("hp", "int")]),
            Virtual_Asm("addi", 3, [Reg("hp", "int"), Reg("hp", "int"), Reg(str(4 * (fv_length + 1)), "int")]),
        ] + put_asm + Closure_t2VirtualAsm_loop(closure_t.e, fundefs)
    
    elif typ is closure.AppCls:
        # 自由変数でない引数を，int,floatに分けて順番に取り出す
        int_list, float_list = separateIntAndFloat(closure_t.args)
        return [
            Virtual_Asm(
                "app_cls",
                len(int_list + float_list) + 2,
                [
                    Reg("!", "unknown"), Reg(closure_t.var, "int")
                ] + [
                    Reg(i, "int") for i in int_list # intの引数
                ] + [
                    Reg(f, "float") for f in float_list # floatの引数
                ])
        ]

    elif typ is closure.AppDir:
        # 引数をint,floatに分けて順番に取り出す
        int_list, float_list = separateIntAndFloat(closure_t.args)
        return [
            Virtual_Asm(
                "app_dir",
                len(int_list + float_list) + 2,
                [
                    Reg("!", "unknown"),
                    Reg(closure_t.var, "label")
                ] + [
                    Reg(i, "int") for i in int_list
                ] + [
                    Reg(f, "float") for f in float_list
                ])
        ]
    
    # タプルをヒープ上に作成する
    elif typ is closure.Tuple:
        tuple_cnt += 1
        vars_length = len(closure_t.vars)
        # int,floatに分けてこの順でメモリに格納する
        int_list, float_list = separateIntAndFloat(closure_t.vars)
        int_asm = []
        float_asm = []
        idx = 0
        for item in int_list:
            int_asm.append(Virtual_Asm("sw", 3, [Reg("tuple"+str(tuple_cnt), "int"), Reg(item, "int"), Reg(str(4 * idx), "int")]))
            idx += 1
        for item in float_list:
            float_asm.append(Virtual_Asm("fsw", 3, [Reg("tuple"+str(tuple_cnt), "int"), Reg(item, "float"), Reg(str(4 * idx), "int")]))
            idx += 1
        env.set("tuple"+str(tuple_cnt), "int")
        # int_asm: intの引数をヒープ上に作る
        # float_asm: floatの引数をヒープ上に作る
        return [
            Virtual_Asm("mv", 2, [Reg("tuple"+str(tuple_cnt), "int"), Reg("hp", "int")]),
            Virtual_Asm("addi", 3, [Reg("hp", "int"), Reg("hp", "int"), Reg(str(4 * vars_length), "int")]),
        ] + int_asm + float_asm + [
            Virtual_Asm("mv", 2, [Reg("!", "int"), Reg("tuple"+str(tuple_cnt), "int")]),
        ]
    
    # ヒープ上のタプルから要素を取り出す
    elif typ is closure.LetTuple:
        # タプルの中に含まれる全ての変数の型情報をenvに登録する
        for var in closure_t.vars:
            env.set(var[0], var[1])
        # int,floatに分けてこの順でメモリから取り出す
        int_vars, float_vars = separateIntAndFloat([var[0] for var in closure_t.vars])
        first_asm = []
        idx = 0
        for int_var in int_vars:
            first_asm.append(Virtual_Asm("lw", 3, [Reg(int_var, "int"), Reg(closure_t.var, "int"), Reg(str(idx * 4), "int")]))
            idx += 1
        for float_var in float_vars:
            first_asm.append(Virtual_Asm("flw", 3, [Reg(float_var, "float"), Reg(closure_t.var, "int"), Reg(str(idx * 4), "int")]))
            idx += 1
        # first_asm: タプルの要素を取り出す命令列
        return first_asm + Closure_t2VirtualAsm_loop(closure_t.e, fundefs)
    
    # 配列の要素を取り出す
    elif typ is closure.Get:
        get_cnt += 1
        env.set("get1."+str(get_cnt), "int")
        env.set("get2."+str(get_cnt), "int")
        # アドレスvar1 + var2 * 4を計算して、メモリ上のそのアドレスにあるものを取り出す
        return [
            Virtual_Asm("slli", 3, [Reg("get1."+str(get_cnt), "int"), Reg(closure_t.var2, "int"), Reg("2", "int")]),
            Virtual_Asm("add", 3, [Reg("get2."+str(get_cnt), "int"), Reg(closure_t.var1, "int"), Reg("get1."+str(get_cnt), "int")]),
            Virtual_Asm("lw_or_flw", 3, [Reg("!", "unknown"), Reg("get2."+str(get_cnt), "int"), Reg("0", "int")])
        ]
    
    # 配列に値をセットする
    elif typ is closure.Put:
        put_cnt += 1
        env.set("put1."+str(put_cnt), "int")
        env.set("put2."+str(put_cnt), "int")
        return [
            Virtual_Asm("slli", 3, [Reg("put1."+str(put_cnt), "int"), Reg(closure_t.var2, "int"), Reg("2", "int")]),
            Virtual_Asm("add", 3, [Reg("put2."+str(put_cnt), "int"), Reg(closure_t.var1, "int"), Reg("put1."+str(put_cnt), "int")]),
        ] + [
            Virtual_Asm("fsw", 3, [Reg("put2."+str(put_cnt), "int"), Reg(closure_t.var3, "float"), Reg("0", "int")]) if env.get(closure_t.var3) == "float" else
            Virtual_Asm("sw", 3, [Reg("put2."+str(put_cnt), "int"), Reg(closure_t.var3, "int"), Reg("0", "int")])
        ]

    else:
        error.error("Invalid Closure Type.")

# closure.Fundefを仮想アセンブリ列に落とし込む
def Fundef2VirtualAsm (fundef:closure.Fundef, fundefs) -> List[Virtual_Asm]:
    global fundef_cnt
    env.set(fundef.name[0], fundef.name[1])
    fundef_cnt += 1

    # 返り値を返す命令を生成
    ret_type = retrieveRetType(fundef.name[1])
    if ret_type == "()":
        last_asm = [Virtual_Asm("ret_unit", 0, [])]  
    elif ret_type == "float":
        last_asm = [Virtual_Asm("ret", 1, [Reg("ret_reg"+str(fundef_cnt), "float")])]
    else:
        last_asm = [Virtual_Asm("ret", 1, [Reg("ret_reg"+str(fundef_cnt), "int")])]
    # 自由変数を取り出す
    formal_fv_int_list = []
    formal_fv_float_list = []
    for fv in fundef.formal_fv:
        env.set(fv[0], fv[1])
        if fv[1] == "int":
            formal_fv_int_list.append(fv[0])
        elif fv[1] == "float":
            formal_fv_float_list.append(fv[0])
        else:
            formal_fv_int_list.append(fv[0])
    # # 自己再帰で使われる場合があるのでラベルを保持しておく（必要なければremoveUnnecessaryInstrで取り除かれるので問題なし，例えば関数のアドレスやクロージャを配列に入れるとき等に必要になる）
    # クロージャを格納しておく
    recursive_asm = [Virtual_Asm("mv", 2, [Reg(fundef.name[0], "int"), Reg("cls_address" + str(fundef_cnt), "label")])]
    # 変数の型をenvに登録
    for arg in fundef.args:
        env.set(arg[0], arg[1])
    args_int_list, args_float_list = separateIntAndFloat(list(map(lambda x: x[0], fundef.args)))
    # recursive_asm: 自己再帰で使われる場合に備えて自身のラベルを保持する命令
    # last_asm: 返り値を返すことを含めたretの命令
    return [
        Virtual_Asm(fundef.name[0] + ":", 0, []),
    ] + [
        Virtual_Asm("* args", 1, [Reg(arg, 'int')]) for arg in args_int_list
    ] + [
        Virtual_Asm("* args", 1, [Reg(arg, 'float')]) for arg in args_float_list
    ] + [
        Virtual_Asm("* formal_fv", 1, [Reg(arg, 'int')]) for arg in formal_fv_int_list
    ] + [
        Virtual_Asm("* formal_fv", 1, [Reg(arg, 'float')]) for arg in formal_fv_float_list
    ] + recursive_asm + replaceAllExcl(
        Closure_t2VirtualAsm_loop(fundef.body, fundefs),
        Reg("ret_reg"+str(fundef_cnt), ret_type)
    ) + last_asm

# List[closure.Fundef]を仮想アセンブリ列に落とし込む
def Fundefs2VirtualAsm (fundefs:List[closure.Fundef]) -> List[List[Virtual_Asm]]:
    ret = []
    for fundef in fundefs:
        ret.append(Fundef2VirtualAsm(fundef, fundefs))
    return ret

# デバッグ用
def VirtualAsmList2Str (lis:List[Virtual_Asm]) -> str:
    ret = ""
    for virtual_asm in lis:
        if ":" in virtual_asm.instr_name: # label
            ret += virtual_asm.instr_name
        elif "#" in virtual_asm.instr_name: # comment
            ret += virtual_asm.instr_name
        else:
            ret += "\t" + virtual_asm.instr_name + " " + ", ".join([reg.name + "(" + reg.typ + ")" for reg in virtual_asm.arg_list])
        ret += "\n"
    return ret
