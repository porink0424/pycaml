#--------------------------------------------------
#
# lib.py
# minrtの実行のために必要な組み込み関数のアセンブリコードデータ
#
#--------------------------------------------------

instrs = {
    # 大きさがa1で，全ての要素がa2(int)の配列を作成し，その先頭のポインタを返す関数
    "min_caml_create_array" : {
        "ret_type" : "int",
        "used_regs_set_int" : {"a1", "a2", "a3", "a4"},
        "used_regs_set_float" : {},
        "body" : "min_caml_create_array:\n" \
            + "\tmv a3, hp\n" \
            + "\tbeq a1, x0, end_loop_min_caml_create_array\n" \
            + "\tslli a1, a1, 2\n" \
            + "\tadd hp, hp, a1\n" \
            + "\tli a1, 0\n" \
            + "\tmv a4, a3\n" \
            + "loop_min_caml_create_array:\n" \
            + "\tsw a2, 0(a4)\n" \
            + "\taddi a1, a1, 4\n" \
            + "\tadd a4, a1, a3\n" \
            + "\tbne hp, a4, loop_min_caml_create_array\n" \
            + "end_loop_min_caml_create_array:\n" \
            + "\tmv a1, a3\n" \
            + "\tret\n",
    },
    # 大きさがa1で，全ての要素がfa0(float)の配列を作成し，その先頭のポインタを返す関数
    "min_caml_create_float_array" : {
        "ret_type" : "int",
        "used_regs_set_int" : {"a1", "a2", "a4"},
        "used_regs_set_float" : {"fa0"},
        "body" : "min_caml_create_float_array:\n" \
            + "\tmv a2, hp\n" \
            + "\tbeq a1, x0, end_loop_min_caml_create_float_array\n" \
            + "\tslli a1, a1, 2\n" \
            + "\tadd hp, hp, a1\n" \
            + "\tli a1, 0\n" \
            + "\tmv a4, a2\n" \
            + "loop_min_caml_create_float_array:\n" \
            + "\tfsw fa0, 0(a4)\n" \
            + "\taddi a1, a1, 4\n" \
            + "\tadd a4, a1, a2\n" \
            + "\tbne hp, a4, loop_min_caml_create_float_array\n" \
            + "end_loop_min_caml_create_float_array:\n" \
            + "\tmv a1, a2\n" \
            + "\tret\n",
    },
    # float_of_int
    "min_caml_float_of_int" : {
        "ret_type" : "float",
        "used_regs_set_int" : {"a1"},
        "used_regs_set_float" : {"fa0"},
        "body" : "min_caml_float_of_int:\n" \
            + "\tfcvt.s.w fa0, a1\n" \
            + "\tret\n",
    },
    # int_of_float
    "min_caml_int_of_float" : {
        "ret_type" : "int",
        "used_regs_set_int" : {"a1"},
        "used_regs_set_float" : {"fa0"},
        "body" : "min_caml_int_of_float:\n" \
            + "\tfcvt.w.s a1, fa0\n" \
            + "\tret\n",
    },
    # fless
    "min_caml_fless" : {
        "ret_type" : "int",
        "used_regs_set_int" : {"a1"},
        "used_regs_set_float" : {"fa0", "fa1"},
        "body" : "min_caml_fless:\n" \
            + "\tflt a1, fa0, fa1\n" \
            + "\tret\n",
    },
    # fneg
    "min_caml_fneg" : {
        "ret_type" : "float",
        "used_regs_set_int" : {},
        "used_regs_set_float" : {"fa0"},
        "body" : "min_caml_fneg:\n" \
            + "\tfsgnjn fa0, fa0, fa0\n" \
            + "\tret\n",
    },
    # fsqr
    "min_caml_fsqr" : {
        "ret_type" : "float",
        "used_regs_set_int" : {},
        "used_regs_set_float" : {"fa0"},
        "body" : "min_caml_fsqr:\n" \
            + "\tfmul fa0, fa0, fa0\n" \
            + "\tret\n",
    },
    # fabs
    "min_caml_fabs" : {
        "ret_type" : "float",
        "used_regs_set_int" : {},
        "used_regs_set_float" : {"fa0"},
        "body" : "min_caml_fabs:\n" \
            + "\tfsgnjx fa0, fa0, fa0\n" \
            + "\tret\n",
    },
	# fsgnj
	"min_caml_fsgnj" : {
		"ret_type" : "float",
        "used_regs_set_int" : {},
        "used_regs_set_float" : {"fa0"},
        "body" : "min_caml_fsgnj:\n" \
            + "\tfsgnj fa0, fa0, fa0\n" \
            + "\tret\n",
	},
    # floor
    "min_caml_floor" : {
        "ret_type" : "float",
        "used_regs_set_int" : {"a1"},
        "used_regs_set_float" : {"fa0", "fa1"},
        "body" : "min_caml_floor:\n" \
            + "\tfcvt.w.s a1, fa0\n" \
            + "\tfcvt.s.w fa1, a1\n" \
            + "\tfle a1, fa1, fa0\n" \
            + "\tbeq a1, x0, min_caml_floor_else\n" \
            + "\tfmv fa0, fa1\n" \
            + "\tret\n" \
            + "min_caml_floor_else:\n" \
            + "\tli a1, 1065353216 # 1.0\n" \
            + "\tfmv.w.x fa0, a1\n" \
            + "\tfsub fa0, fa1, fa0\n" \
			+ "\tfcvt.w.s a1, fa0\n" \
            + "\tfcvt.s.w fa1, a1\n" \
            + "\tret\n",
    },
    # fhalf
    "min_caml_fhalf" : {
        "ret_type" : "float",
        "used_regs_set_int" : {"a1"},
        "used_regs_set_float" : {"fa0", "fa1"},
        "body" : "min_caml_fhalf:\n" \
            + "\tli a1, 1056964608 # 0.5\n" \
            + "\tfmv.w.x fa1, a1\n" \
            + "\tfmul fa0, fa0, fa1\n" \
            + "\tret\n",
    },
    # sqrt
    "min_caml_sqrt" : {
        "ret_type" : "float",
        "used_regs_set_int" : {},
        "used_regs_set_float" : {"fa0"},
        "body" : "min_caml_sqrt:\n" \
            + "\tfsqrt fa0, fa0\n" \
            + "\tret\n",
    },
    # fisneg
    "min_caml_fisneg" : {
        "ret_type" : "int",
        "used_regs_set_int" : {"a1"},
        "used_regs_set_float" : {"fa0", "fa1"},
        "body" : "min_caml_fisneg:\n" \
            + "\tfmv.w.x fa1, x0\n" \
            + "\tflt a1, fa0, fa1\n" \
            + "\tret\n",
    },
    # fispos
    "min_caml_fispos" : {
        "ret_type" : "int",
        "used_regs_set_int" : {"a1"},
        "used_regs_set_float" : {"fa0", "fa1"},
        "body" : "min_caml_fispos:\n" \
            + "\tfmv.w.x fa1, x0\n" \
            + "\tflt a1, fa1, fa0\n" \
            + "\tret\n",
    },
    # fiszero
    "min_caml_fiszero" : {
        "ret_type" : "int",
        "used_regs_set_int" : {"a1"},
        "used_regs_set_float" : {"fa0", "fa1"},
        "body" : "min_caml_fiszero:\n" \
            + "\tfmv.w.x fa1, x0\n" \
            + "\tfeq a1, fa0, fa1\n" \
            + "\tret\n",
    },
    # print_char
    "min_caml_print_char" : {
        "ret_type" : "()",
        "used_regs_set_int" : {"a1"},
        "used_regs_set_float" : {},
        "body" : "min_caml_print_char:\n" \
            + "\tsw a1, 0(x0)\n" \
            + "\tret\n",
    },
    # print_int
    "min_caml_print_int" : {
        "ret_type" : "()",
        "used_regs_set_int" : {"a1", "a2", "a3", "a4"},
        "used_regs_set_float" : {},
        "body" : "min_caml_print_int:\n" \
			+ "\tli a2, 0\n" \
            + "\tli a3, 0\n" \
            + "\tli a4, 100\n" \
            + "min_caml_print_int_hundreds:\n" \
            + "\tblt a1, a4, min_caml_print_int_tens_pre\n" \
            + "\tsub a1, a1, a4\n" \
            + "\taddi a2, a2, 1\n" \
            + "\tj min_caml_print_int_hundreds\n" \
            + "min_caml_print_int_tens_pre:\n" \
            + "\tli a4, 10\n" \
            + "min_caml_print_int_tens:\n" \
            + "\tblt a1, a4, min_caml_print_int_ones\n" \
            + "\tsub a1, a1, a4\n" \
            + "\taddi a3, a3, 1\n" \
            + "\tj min_caml_print_int_tens\n" \
            + "min_caml_print_int_ones:\n" \
            + "\taddi a2, a2, 48\n" \
            + "\tsw a2, 0(x0)\n" \
            + "\taddi a3, a3, 48\n" \
            + "\tsw a3, 0(x0)\n" \
            + "\taddi a1, a1, 48\n" \
            + "\tsw a1, 0(x0)\n" \
            + "\tret\n",
    },
    # read_int
    "min_caml_read_int" : {
        "ret_type" : "int",
        "used_regs_set_int" : {"a1", "a2"},
        "used_regs_set_float" : {},
        "body" : "min_caml_read_int:\n" \
            + "\tlw a1, 0(x0)\n" \
            + "\tlw a2, 0(x0)\n" \
            + "\tslli a1, a1, 8\n" \
            + "\tor a1, a1, a2\n" \
            + "\tlw a2, 0(x0)\n" \
            + "\tslli a1, a1, 8\n" \
            + "\tor a1, a1, a2\n" \
            + "\tlw a2, 0(x0)\n" \
            + "\tslli a1, a1, 8\n" \
            + "\tor a1, a1, a2\n" \
            + "\tret\n",
    },
    # read_float
    "min_caml_read_float" : {
        "ret_type" : "float",
        "used_regs_set_int" : {"a1", "a2"},
        "used_regs_set_float" : {"fa0"},
        "body" : "min_caml_read_float:\n" \
            + "\tlw a1, 0(x0)\n" \
            + "\tlw a2, 0(x0)\n" \
            + "\tslli a1, a1, 8\n" \
            + "\tor a1, a1, a2\n" \
            + "\tlw a2, 0(x0)\n" \
            + "\tslli a1, a1, 8\n" \
            + "\tor a1, a1, a2\n" \
            + "\tlw a2, 0(x0)\n" \
            + "\tslli a1, a1, 8\n" \
            + "\tor a1, a1, a2\n" \
            + "\tfmv.w.x fa0, a1\n" \
            + "\tret\n",
    },
    # debug_float (for debug)
    "min_caml_debug_float" : {
        "ret_type" : "()",
        "used_regs_set_int" : {},
        "used_regs_set_float" : {},
        "body" : "min_caml_debug_float:\n" \
            + "\tret\n",
    },
    # debug_int (for debug)
    "min_caml_debug_int" : {
        "ret_type" : "()",
        "used_regs_set_int" : {},
        "used_regs_set_float" : {},
        "body" : "min_caml_debug_int:\n" \
            + "\tret\n",
    },
}