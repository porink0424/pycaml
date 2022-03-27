#--------------------------------------------------
#
# error.py
# エラーの出力・プログラムの異常終了を担う
#
#--------------------------------------------------

import sys
import inspect

def error (message:str):
    print("Error Massage from {} in {}:".format(inspect.stack()[1].function, inspect.stack()[1].filename))
    print(message)
    print("\nStop.")
    sys.exit(1)