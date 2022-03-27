#--------------------------------------------------
#
# reglist.py
# 使えるレジスタのリストのデータ（先頭から優先的に使われていく）
#
#--------------------------------------------------

# 使用方法が決まっているのでレジスタ割り当て等で解析に含めない特別なレジスタの集合
SPECIAL_INT_REGS = {
    'hp', 'x0', 'x25', 'x26', 'x27'
}
SPECIAL_FLOAT_REGS = {
    'f25', 'f26', 'f27'
}

INT_REGS_FOR_FUNC = [
    # caller-saveのレジスタ
    'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7',
    'x5', 'x6', 'x7',
    'x28', 'x29', 'x30', 'x31',
    # callee-saveのレジスタ（行き返りでスタックにstore/restoreしなければならないのでできればつかいたくないレジスタ）
    'x8', 'x9',
    'x18', 'x19', 'x20', 'x21', 'x22', 'x23', 'x24',
]
# 以下の変数idx以降のレジスタについては状態を保持したまま返さなければならない
INT_REGS_FOR_FUNC_RESPONSIBLE_IDX = 14

FLOAT_REGS_FOR_FUNC = [
    # caller-saveのレジスタ
    'fa0', 'fa1', 'fa2', 'fa3', 'fa4', 'fa5', 'fa6', 'fa7',
    'f0', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7',
    'f28', 'f29', 'f30', 'f31',
    # callee-saveのレジスタ
    'f8', 'f9',
    'f18', 'f19', 'f20', 'f21', 'f22', 'f23', 'f24',
]
FLOAT_REGS_FOR_FUNC_RESPONSIBLE_IDX = 20

INT_REGS_FOR_MAIN = [
    # callee-save
    'x8', 'x9',
    'x18', 'x19', 'x20', 'x21', 'x22', 'x23', 'x24',
    # caller-save
    'x5', 'x6', 'x7',
    'x28', 'x29', 'x30', 'x31',
    # 引数レジスタはできるだけ使わない方が良い
    'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7',
]
INT_REGS_FOR_MAIN_RESPONSIBLE_IDX = 9

FLOAT_REGS_FOR_MAIN = [
    # callee-save
    'f8', 'f9',
    'f18', 'f19', 'f20', 'f21', 'f22', 'f23', 'f24',
    # caller-save
    'f0', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7',
    'f28', 'f29', 'f30', 'f31',
    # 引数レジスタはできるだけ使わない方が良い
    'fa0', 'fa1', 'fa2', 'fa3', 'fa4', 'fa5', 'fa6', 'fa7',
]
FLOAT_REGS_FOR_MAIN_RESPONSIBLE_IDX = 9