#--------------------------------------------------
#
# closure.py
# closure変換まで行われたデータを文字列からpythonのデータ構造に変換する
#
#--------------------------------------------------

from typing import List
import re

class Closure_t:
    def __init__ (self):
        pass

class Unit (Closure_t):
    def __init__ (self):
        pass

class Int (Closure_t):
    def __init__ (self, val:int):
        self.val = val

class Float (Closure_t):
    def __init__ (self, val:float):
        self.val = val

class Neg (Closure_t):
    def __init__ (self, var:str):
        self.var = var

class Add (Closure_t):
    def __init__ (self, var1:str, var2:str):
        self.var1 = var1
        self.var2 = var2

class Sub (Closure_t):
    def __init__ (self, var1:str, var2:str):
        self.var1 = var1
        self.var2 = var2

class Mul (Closure_t):
    def __init__ (self, var1:str, var2:str):
        self.var1 = var1
        self.var2 = var2

class Div (Closure_t):
    def __init__ (self, var1:str, var2:str):
        self.var1 = var1
        self.var2 = var2

class FNeg (Closure_t):
    def __init__ (self, var:str):
        self.var = var

class FAdd (Closure_t):
    def __init__ (self, var1:str, var2:str):
        self.var1 = var1
        self.var2 = var2

class FSub (Closure_t):
    def __init__ (self, var1:str, var2:str):
        self.var1 = var1
        self.var2 = var2

class FMul (Closure_t):
    def __init__ (self, var1:str, var2:str):
        self.var1 = var1
        self.var2 = var2

class FDiv (Closure_t):
    def __init__ (self, var1:str, var2:str):
        self.var1 = var1
        self.var2 = var2

class IfEq (Closure_t):
    def __init__ (self, var1:str, var2:str, e1:Closure_t, e2:Closure_t):
        self.var1 = var1
        self.var2 = var2
        self.e1 = e1
        self.e2 = e2

class IfNEq (Closure_t):
    def __init__ (self, var1:str, var2:str, e1:Closure_t, e2:Closure_t):
        self.var1 = var1
        self.var2 = var2
        self.e1 = e1
        self.e2 = e2

class IfLE (Closure_t):
    def __init__ (self, var1:str, var2:str, e1:Closure_t, e2:Closure_t):
        self.var1 = var1
        self.var2 = var2
        self.e1 = e1
        self.e2 = e2

class IfLT (Closure_t):
    def __init__ (self, var1:str, var2:str, e1:Closure_t, e2:Closure_t):
        self.var1 = var1
        self.var2 = var2
        self.e1 = e1
        self.e2 = e2

class Let (Closure_t):
    def __init__ (self, var:str, type:str, e1:Closure_t, e2:Closure_t):
        self.var = var
        self.type = type
        self.e1 = e1
        self.e2 = e2

class Var (Closure_t):
    def __init__ (self, var:str):
        self.var = var

class Closure:
    def __init__ (self, entry:str, actual_fv:List[str]):
        self.entry = entry
        self.actual_fv = actual_fv

class MakeCls (Closure_t):
    def __init__ (self, var:str, type:str, closure:Closure, e:Closure_t):
        self.var = var
        self.type = type
        self.closure = closure
        self.e = e

class AppCls (Closure_t):
    def __init__ (self, var:str, args:List[str]):
        self.var = var
        self.args = args

class AppDir (Closure_t):
    def __init__ (self, var:str, args:List[str]):
        self.var = var
        self.args = args

class Tuple (Closure_t):
    def __init__ (self, vars:List[str]):
        self.vars = vars

class LetTuple (Closure_t):
    def __init__ (self, vars, var:str, e:Closure_t):
        self.vars = vars
        self.var = var
        self.e = e

class Get (Closure_t):
    def __init__ (self, var1:str, var2:str):
        self.var1 = var1
        self.var2 = var2

class Put (Closure_t):
    def __init__ (self, var1:str, var2:str, var3:str):
        self.var1 = var1
        self.var2 = var2
        self.var3 = var3

class ExtArray (Closure_t):
    def __init__ (self, var:str):
        self.var = var

class Fundef:
    def __init__ (self, name:List[str], args:List[List[str]], formal_fv, body:Closure_t):
        self.name = name
        self.args = args
        self.formal_fv = formal_fv
        self.body = body

class Prog:
    def __init__ (self, fundefs:List[Fundef], e:Closure_t, first_hp:int):
        self.fundefs = fundefs
        self.e = e
        self.first_hp = first_hp

# パースの補助関数
# strからList[str]に変換する
def explode (text:str) -> List[str]:
    if len(text) == 2:
        return []
    
    bras = ['(', '{', '[']
    kets = [')', '}', ']']
    idx = 0
    while text[idx] not in bras:
        idx += 1
    separators_idx = [idx] # set positions of , ( ) 

    count = 0
    for i in range(idx + 1, len(text)):
        if text[i] in bras:
            count += 1
        elif text[i] in kets:
            count -= 1
        elif text[i] == ',' and count == 0:
            separators_idx.append(i)
    if text[-2] != ',': # 最後の要素のあとにもコンマがついている場合に対応
        separators_idx.append(len(text) - 1)

    # 取得したコンマの位置から実際にリストを作成する
    ret = []
    for i in range(len(separators_idx) - 1):
        ret.append(text[(separators_idx[i]+1):(separators_idx[i+1])])
    return ret

def str2Closure (text:str) -> Closure:
    if re.match(r"^\{(.*)\}", text) != None:
        entry = re.search(r'\{entry:(.*?),', text).group(1)
        actual_fv = re.search(r'actual_fv:(.*?)\}', text).group(1)
        actual_fv_list = explode(actual_fv)
        return Closure(entry, actual_fv_list)

def str2Closure_t (text:str) -> Closure_t:
    if re.match(r"^Unit", text) != None:
        return Unit()
    elif re.match(r"^Int\((.*)\)", text) != None:
        exploded_lis = explode(text)
        return Int(int(exploded_lis[0]))
    elif re.match(r"^Float\((.*)\)", text) != None:
        exploded_lis = explode(text)
        return Float(float(exploded_lis[0]))
    elif re.match(r"^Neg\((.*)\)", text) != None:
        exploded_lis = explode(text)
        return Neg(exploded_lis[0])
    elif re.match(r"^Add\((.*)\)", text) != None:
        exploded_lis = explode(text)
        return Add(exploded_lis[0], exploded_lis[1])
    elif re.match(r"^Sub\((.*)\)", text) != None:
        exploded_lis = explode(text)
        return Sub(exploded_lis[0], exploded_lis[1])
    elif re.match(r"^Mul\((.*)\)", text) != None:
        exploded_lis = explode(text)
        return Mul(exploded_lis[0], exploded_lis[1])
    elif re.match(r"^Div\((.*)\)", text) != None:
        exploded_lis = explode(text)
        return Div(exploded_lis[0], exploded_lis[1])
    elif re.match(r"^FNeg\((.*)\)", text) != None:
        exploded_lis = explode(text)
        return FNeg(exploded_lis[0])
    elif re.match(r"^FAdd\((.*)\)", text) != None:
        exploded_lis = explode(text)
        return FAdd(exploded_lis[0], exploded_lis[1])
    elif re.match(r"^FSub\((.*)\)", text) != None:
        exploded_lis = explode(text)
        return FSub(exploded_lis[0], exploded_lis[1])
    elif re.match(r"^FMul\((.*)\)", text) != None:
        exploded_lis = explode(text)
        return FMul(exploded_lis[0], exploded_lis[1])
    elif re.match(r"^FDiv\((.*)\)", text) != None:
        exploded_lis = explode(text)
        return FDiv(exploded_lis[0], exploded_lis[1])
    elif re.match(r"^IfEq\((.*)\)", text) != None:
        exploded_lis = explode(text)
        e1 = str2Closure_t(exploded_lis[2])
        e2 = str2Closure_t(exploded_lis[3])
        return IfEq(exploded_lis[0], exploded_lis[1], e1, e2)
    elif re.match(r"^IfNEq\((.*)\)", text) != None:
        exploded_lis = explode(text)
        e1 = str2Closure_t(exploded_lis[2])
        e2 = str2Closure_t(exploded_lis[3])
        return IfNEq(exploded_lis[0], exploded_lis[1], e1, e2)
    elif re.match(r"^IfLE\((.*)\)", text) != None:
        exploded_lis = explode(text)
        e1 = str2Closure_t(exploded_lis[2])
        e2 = str2Closure_t(exploded_lis[3])
        return IfLE(exploded_lis[0], exploded_lis[1], e1, e2)
    elif re.match(r"^IfLT\((.*)\)", text) != None:
        exploded_lis = explode(text)
        e1 = str2Closure_t(exploded_lis[2])
        e2 = str2Closure_t(exploded_lis[3])
        return IfLT(exploded_lis[0], exploded_lis[1], e1, e2)
    elif re.match(r"^Let\((.*)\)", text) != None:
        exploded_lis = explode(text)
        var_type = explode(exploded_lis[0])
        var = var_type[0]
        type = var_type[1]
        e1 = str2Closure_t(exploded_lis[1])
        e2 = str2Closure_t(exploded_lis[2])
        return Let(var, type, e1, e2)
    elif re.match(r"^Var\((.*)\)", text) != None:
        exploded_lis = explode(text)
        return Var(exploded_lis[0])
    elif re.match(r"^MakeCls\((.*)\)", text) != None:
        exploded_lis = explode(text)
        var_type = explode(exploded_lis[0])
        var = var_type[0]
        type = var_type[1]
        closure = str2Closure(exploded_lis[1])
        e = str2Closure_t(exploded_lis[2])
        return MakeCls(var, type, closure, e)
    elif re.match(r"^AppCls\((.*)\)", text) != None:
        exploded_lis = explode(text)
        args = explode(exploded_lis[1])
        return AppCls(exploded_lis[0], args)
    elif re.match(r"^AppDir\((.*)\)", text) != None:
        exploded_lis = explode(text)
        args = explode(exploded_lis[1])
        return AppDir(exploded_lis[0], args)
    elif re.match(r"^Tuple\((.*)\)", text) != None:
        exploded_lis = explode(text)
        vars = explode(exploded_lis[0])
        return Tuple(vars)
    elif re.match(r"^LetTuple\((.*)\)", text) != None:
        exploded_lis = explode(text)
        vars_tmp = explode(exploded_lis[0])
        vars = []
        for var in vars_tmp:
            vars.append(explode(var))
        e = str2Closure_t(exploded_lis[2])
        return LetTuple(vars, exploded_lis[1], e)
    elif re.match(r"^Get\((.*)\)", text) != None:
        exploded_lis = explode(text)
        return Get(exploded_lis[0], exploded_lis[1])
    elif re.match(r"^Put\((.*)\)", text) != None:
        exploded_lis = explode(text)
        return Put(exploded_lis[0], exploded_lis[1], exploded_lis[2])
    elif re.match(r"^ExtArray\((.*)\)", text) != None:
        exploded_lis = explode(text)
        return ExtArray(exploded_lis[0])

def str2Fundef_list (text:str) -> List[Fundef]:
    fundefs = explode(text)
    ret = []
    for fundef in fundefs:
        name = explode(re.search(r'name:(.*),args', fundef).group(1))
        args_tmp = explode(re.search(r'args:(.*),formal_fv', fundef).group(1))
        args = []
        for arg in args_tmp:
            args.append(explode(arg))
        formal_fv_tmp = explode(re.search(r'formal_fv:(.*),body', fundef).group(1))
        formal_fv = []
        for fv in formal_fv_tmp:
            formal_fv.append(explode(fv))
        body = str2Closure_t(re.search(r'body:(.*)\}', fundef).group(1))
        ret.append(Fundef(name, args, formal_fv, body))
    return ret
