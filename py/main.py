#--------------------------------------------------
#
# main.py
# 全体の流れを制御する
#
#--------------------------------------------------

import re
import lib
import reglist
import closure
import constReg
import virtual
import constFold
import peephole
import liveness
import regAlloc
import tail
import inline
import expand
import emit
import argparse
import sys

def main ():
    sys.setrecursionlimit(10 ** 9)
    
    # 実行時引数の設定
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", help="choose a file (in 'test' directory) to compile, the default file is 'test/test'")
    args = parser.parse_args()

    # ファイル読み込み
    if not args.file:
        args.file = "test" # defaultはintermediate/testを読みに行く
    f = open('intermediate/' + args.file + '.txt', 'r')
    text = f.read()
    f.close()

    # パース
    first_hp = int(re.search(r'first_hp : (.*?)\n', text).group(1))
    fundef_list = re.search(r'fundef list:\n(.*?)\n', text).group(1)
    e = re.search(r'\nt:\n(.*)', text).group(1)
    prog = closure.Prog(closure.str2Fundef_list(fundef_list), closure.str2Closure_t(e), first_hp)

    # 定数レジスタ埋め込み
    for fundef in prog.fundefs:
        fundef.body = constReg.constReg(fundef.body, {})
    prog.e = constReg.constReg(prog.e, {})

    # 仮想アセンブリ化
    fundefs_asm = virtual.Fundefs2VirtualAsm(prog.fundefs)
    body_asm = [
        # mainタグ
        virtual.Virtual_Asm("main:", 0, []),
        # global変数のヒープ領域分を確保
        virtual.Virtual_Asm("addi", 3, [virtual.Reg("hp", "int"), virtual.Reg("hp", "int"), virtual.Reg(str(first_hp), "int")]),
        # 定数レジスタの値の格納
        virtual.Virtual_Asm("li", 2, [virtual.Reg("x27", "int"), virtual.Reg("0", "int")]), # 0.0
        virtual.Virtual_Asm("fmv.w.x", 2, [virtual.Reg("f25", "float"), virtual.Reg("x27", "int")]),
        virtual.Virtual_Asm("li", 2, [virtual.Reg("x27", "int"), virtual.Reg("1065353216", "int")]), # 1.0
        virtual.Virtual_Asm("fmv.w.x", 2, [virtual.Reg("f26", "float"), virtual.Reg("x27", "int")]),
        virtual.Virtual_Asm("li", 2, [virtual.Reg("x27", "int"), virtual.Reg("1073741824", "int")]), # 2.0
        virtual.Virtual_Asm("fmv.w.x", 2, [virtual.Reg("f27", "float"), virtual.Reg("x27", "int")]),
        virtual.Virtual_Asm("li", 2, [virtual.Reg("x0", "int"), virtual.Reg("0", "int")]),
        virtual.Virtual_Asm("li", 2, [virtual.Reg("x25", "int"), virtual.Reg("1", "int")]),
        virtual.Virtual_Asm("li", 2, [virtual.Reg("x26", "int"), virtual.Reg("2", "int")]),
        virtual.Virtual_Asm("li", 2, [virtual.Reg("x27", "int"), virtual.Reg("3", "int")]),
    ] + virtual.Closure_t2VirtualAsm(prog.e, prog.fundefs)

    # 整数の定数畳み込み
    for i in range(len(fundefs_asm)):
        fundefs_asm[i] = constFold.constFold(fundefs_asm[i])
    body_asm = constFold.constFold(body_asm)

    # peephole最適化
    for i in range(len(fundefs_asm)):
        fundefs_asm[i] = peephole.peepholeOpt(fundefs_asm[i])
    body_asm = peephole.peepholeOpt(body_asm)

    # レジスタ割り当て
    for i in range(len(fundefs_asm)):
        fundefs_asm[i] = regAlloc.regAlloc(fundefs_asm[i], reglist.INT_REGS_FOR_FUNC, reglist.FLOAT_REGS_FOR_FUNC)
        fundefs_asm[i] = regAlloc.optimizeAllocOfArgs(fundefs_asm[i])
    body_asm = regAlloc.regAlloc(body_asm, reglist.INT_REGS_FOR_MAIN, reglist.FLOAT_REGS_FOR_MAIN)
    body_asm = regAlloc.optimizeAllocOfArgs(body_asm)

    # 末尾呼び出し最適化をかける
    for i in range(len(fundefs_asm)):
        fundefs_asm[i] = tail.tailCallOpt(fundefs_asm[i])
    body_asm = tail.tailCallOpt(body_asm)

    # インライン最適化
    for i in range(len(fundefs_asm)):
        fundefs_asm[i] = inline.inlineOpt(fundefs_asm[i])
    body_asm = inline.inlineOpt(body_asm)

    f.close()

    # store/restore展開,関数呼び出しの展開
    for i in range(len(fundefs_asm)):
        live_int, live_float, _, _, _, _ = liveness.AnalyzeLiveness(fundefs_asm[i])
        expand.set_used_regs_set_in_func(fundefs_asm[i][0].instr_name.replace(":", ""), fundefs_asm[i], live_int, live_float)
    for i in range(len(fundefs_asm)):
        live_int, live_float, _, _, _, _ = liveness.AnalyzeLiveness(fundefs_asm[i])
        fundefs_asm[i], _ = expand.expand(fundefs_asm[i], [], True, live_int, live_float)
    live_int, live_float, _, _, _, _ = liveness.AnalyzeLiveness(body_asm)
    body_asm, _ = expand.expand(body_asm, [], False, live_int, live_float)

    # 最終アセンブリ出力
    asm_str = ".globl main\n\n.text\n\n"
    # libの外部関数の読み出し
    for key in lib.instrs:
        instr = lib.instrs[key]["body"]
        asm_str += instr + "\n"
    for fundef_asm in fundefs_asm:
        asm_str += emit.VirtualAsmList2Str(fundef_asm)
    asm_str += emit.VirtualAsmList2Str(body_asm)
    asm_str += "\n\tebreak\n"

    # ファイル書き込み
    f = open('asm/' + args.file + '.s', 'w')
    f.write(asm_str)
    f.close()

    return

if __name__ == "__main__":
    main()
