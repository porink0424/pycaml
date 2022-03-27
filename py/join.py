#--------------------------------------------------
#
# main.py
# lib.mlとコンパイル対象のファイルを結合する
#
#--------------------------------------------------

import argparse

def main ():
    # 実行時引数の設定
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", help="choose a file (in 'test' directory) to compile, the default file is 'test/test'")
    args = parser.parse_args()

    # ファイル読み込み
    if not args.file:
        args.file = "test" # defaultはtest/testを読みに行く
    f = open('test/' + args.file + '.ml', 'r')
    text = f.read()
    f.close()

    # lib.mlファイル読み込み
    f = open('lib.ml', 'r')
    lib = f.read()
    f.close()

    # ファイル書き込み
    f = open('intermediate/' + args.file + '.ml', 'w')
    f.write(lib + text)
    f.close()

if __name__ == "__main__":
    main()