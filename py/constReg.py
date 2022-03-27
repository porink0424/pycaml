#--------------------------------------------------
#
# constReg.py
# 定数レジスタを埋め込む最適化を行う
#
#--------------------------------------------------

import closure
import copy

# 環境envに対して{key => value}のペアを加える
def add (env, key, value):
    new_env = copy.deepcopy(env)
    new_env[key] = value
    return new_env

# メイン部分
def constReg (closure_t:closure.Closure_t, constenv) -> closure.Closure_t:
    typ = type(closure_t)

    # Varが定数レジスタで置き換えることができる場合、置き換えて返す
    if typ is closure.Var and closure_t.var in constenv:
        return closure.Var(constenv[closure_t.var])

    # Let((x,t), e1, e2)において、e1がIntかFloatであって、対応する定数レジスタがあるとき、xは定数レジスタとして置き換えることができる
    elif typ is closure.Let:
        # e1がIntである場合
        if type(closure_t.e1) is closure.Int:
            if closure_t.e1.val == 0: # 0レジスタに置き換えることができる
                return closure.Let(
                    closure_t.var,
                    closure_t.type,
                    constReg(closure_t.e1, constenv),
                    # e1を0レジスタとして置き換えることができるので、constenvに加えた上で次の計算を進める
                    constReg(closure_t.e2, add(constenv, closure_t.var, "x0"))
                )
            elif closure_t.e1.val == 1: # 1レジスタに置き換えることができる
                return closure.Let(
                    closure_t.var,
                    closure_t.type,
                    constReg(closure_t.e1, constenv),
                    constReg(closure_t.e2, add(constenv, closure_t.var, "x25"))
                )
            elif closure_t.e1.val == 2: # 2レジスタに置き換えることができる
                return closure.Let(
                    closure_t.var,
                    closure_t.type, 
                    constReg(closure_t.e1, constenv),
                    constReg(closure_t.e2, add(constenv, closure_t.var, "x26"))
                )
            elif closure_t.e1.val == 3: # 3レジスタに置き換えることができる
                return closure.Let(
                    closure_t.var,
                    closure_t.type,
                    constReg(closure_t.e1, constenv),
                    constReg(closure_t.e2, add(constenv, closure_t.var, "x27"))
                )
            else: # 対応する定数整数レジスタがないので、環境を変えることなくe2の計算を進める
                return closure.Let(closure_t.var, closure_t.type, constReg(closure_t.e1, constenv), constReg(closure_t.e2, constenv))
        # e1がFloatである場合（以下Intである場合と同じロジック）
        elif type(closure_t.e1) is closure.Float:
            if closure_t.e1.val == 0.0:
                return closure.Let(
                    closure_t.var,
                    closure_t.type,
                    constReg(closure_t.e1, constenv),
                    constReg(closure_t.e2, add(constenv, closure_t.var, "f25"))
                )
            elif closure_t.e1.val == 1.0:
                return closure.Let(
                    closure_t.var,
                    closure_t.type,
                    constReg(closure_t.e1, constenv),
                    constReg(closure_t.e2, add(constenv, closure_t.var, "f26"))
                )
            elif closure_t.e1.val == 2.0:
                return closure.Let(
                    closure_t.var,
                    closure_t.type,
                    constReg(closure_t.e1, constenv),
                    constReg(closure_t.e2, add(constenv, closure_t.var, "f27"))
                )
            else:
                return closure.Let(closure_t.var, closure_t.type, constReg(closure_t.e1, constenv), constReg(closure_t.e2, constenv))
        else: # e1がIntでもFloatでもないので定数レジスタとして置き換えることはできない
            return closure.Let(closure_t.var, closure_t.type, constReg(closure_t.e1, constenv), constReg(closure_t.e2, constenv))

    # If((var1, var2), e1, e2)において、var1とvar2は置き換えられるなら置き換えた上で、e1,e2の計算を進める
    elif typ is closure.IfEq:
        var1 = constenv[closure_t.var1] if closure_t.var1 in constenv else closure_t.var1
        var2 = constenv[closure_t.var2] if closure_t.var2 in constenv else closure_t.var2
        return closure.IfEq(var1, var2, constReg(closure_t.e1, constenv), constReg(closure_t.e2, constenv))
    elif typ is closure.IfNEq:
        var1 = constenv[closure_t.var1] if closure_t.var1 in constenv else closure_t.var1
        var2 = constenv[closure_t.var2] if closure_t.var2 in constenv else closure_t.var2
        return closure.IfNEq(var1, var2, constReg(closure_t.e1, constenv), constReg(closure_t.e2, constenv))
    elif typ is closure.IfLE:
        var1 = constenv[closure_t.var1] if closure_t.var1 in constenv else closure_t.var1
        var2 = constenv[closure_t.var2] if closure_t.var2 in constenv else closure_t.var2
        return closure.IfLE(var1, var2, constReg(closure_t.e1, constenv), constReg(closure_t.e2, constenv))
    elif typ is closure.IfLT:
        var1 = constenv[closure_t.var1] if closure_t.var1 in constenv else closure_t.var1
        var2 = constenv[closure_t.var2] if closure_t.var2 in constenv else closure_t.var2
        return closure.IfLT(var1, var2, constReg(closure_t.e1, constenv), constReg(closure_t.e2, constenv))

    elif typ is closure.LetTuple:
        return closure.LetTuple(closure_t.vars, closure_t.var, constReg(closure_t.e, constenv))

    # 引数を置き換えられるなら置き換える
    elif typ is closure.Add:
        x = constenv[closure_t.var1] if closure_t.var1 in constenv else closure_t.var1
        y = constenv[closure_t.var2] if closure_t.var2 in constenv else closure_t.var2
        return closure.Add(x, y)
    elif typ is closure.Sub:
        x = constenv[closure_t.var1] if closure_t.var1 in constenv else closure_t.var1
        y = constenv[closure_t.var2] if closure_t.var2 in constenv else closure_t.var2
        return closure.Sub(x, y)
    elif typ is closure.Mul:
        x = constenv[closure_t.var1] if closure_t.var1 in constenv else closure_t.var1
        y = constenv[closure_t.var2] if closure_t.var2 in constenv else closure_t.var2
        return closure.Mul(x, y)
    elif typ is closure.Div:
        x = constenv[closure_t.var1] if closure_t.var1 in constenv else closure_t.var1
        y = constenv[closure_t.var2] if closure_t.var2 in constenv else closure_t.var2
        return closure.Div(x, y)
    elif typ is closure.FAdd:
        x = constenv[closure_t.var1] if closure_t.var1 in constenv else closure_t.var1
        y = constenv[closure_t.var2] if closure_t.var2 in constenv else closure_t.var2
        return closure.FAdd(x, y)
    elif typ is closure.FSub:
        x = constenv[closure_t.var1] if closure_t.var1 in constenv else closure_t.var1
        y = constenv[closure_t.var2] if closure_t.var2 in constenv else closure_t.var2
        return closure.FSub(x, y)
    elif typ is closure.FMul:
        x = constenv[closure_t.var1] if closure_t.var1 in constenv else closure_t.var1
        y = constenv[closure_t.var2] if closure_t.var2 in constenv else closure_t.var2
        return closure.FMul(x, y)
    elif typ is closure.FDiv:
        x = constenv[closure_t.var1] if closure_t.var1 in constenv else closure_t.var1
        y = constenv[closure_t.var2] if closure_t.var2 in constenv else closure_t.var2
        return closure.FDiv(x, y)

    # タプルの要素を置き換えられるなら置き換える
    elif typ is closure.Tuple:
        vars = [constenv[var] if var in constenv else var for var in closure_t.vars]
        return closure.Tuple(vars)

    # todo:  以下はなぜかない方が命令数が下がる・・・→原因究明したい
    # elif typ is closure.Get:
    #     x = constenv[closure_t.var1] if closure_t.var1 in constenv else closure_t.var1
    #     y = constenv[closure_t.var2] if closure_t.var2 in constenv else closure_t.var2
    #     return closure.Get(x, y)
    # elif typ is closure.Put:
    #     x = constenv[closure_t.var1] if closure_t.var1 in constenv else closure_t.var1
    #     y = constenv[closure_t.var2] if closure_t.var2 in constenv else closure_t.var2
    #     z = constenv[closure_t.var3] if closure_t.var3 in constenv else closure_t.var3
    #     return closure.Put(x, y, z)
    
    else:
        return closure_t
