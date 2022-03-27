let limit = ref 1000

let rec iter n e = (* 最適化処理をくりかえす *)
  Format.eprintf "iteration %d@." n;
  if n = 0 then e else
  let e' = Elim.f (ConstFold.f (Inline.f (Assoc.f (Beta.f e)))) in
  if e = e' then e else
  iter (n - 1) e'

let load_ext_funcs _ = (* 外部関数の型を読み込む *)
  Typing.extenv := M.add "float_of_int" (Type.Fun([Type.Int], Type.Float)) !Typing.extenv;
  Typing.extenv := M.add "int_of_float" (Type.Fun([Type.Float], Type.Int)) !Typing.extenv;
  Typing.extenv := M.add "fless" (Type.Fun([Type.Float;Type.Float], Type.Bool)) !Typing.extenv;
  Typing.extenv := M.add "fneg" (Type.Fun([Type.Float], Type.Float)) !Typing.extenv;
  Typing.extenv := M.add "fsqr" (Type.Fun([Type.Float], Type.Float)) !Typing.extenv;
  Typing.extenv := M.add "fabs" (Type.Fun([Type.Float], Type.Float)) !Typing.extenv;
  Typing.extenv := M.add "floor" (Type.Fun([Type.Float], Type.Float)) !Typing.extenv;
  Typing.extenv := M.add "fhalf" (Type.Fun([Type.Float], Type.Float)) !Typing.extenv;
  Typing.extenv := M.add "fsgnj" (Type.Fun([Type.Float], Type.Float)) !Typing.extenv;
  Typing.extenv := M.add "sqrt" (Type.Fun([Type.Float], Type.Float)) !Typing.extenv;
  Typing.extenv := M.add "sin" (Type.Fun([Type.Float], Type.Float)) !Typing.extenv;
  Typing.extenv := M.add "cos" (Type.Fun([Type.Float], Type.Float)) !Typing.extenv;
  Typing.extenv := M.add "atan" (Type.Fun([Type.Float], Type.Float)) !Typing.extenv;
  Typing.extenv := M.add "fisneg" (Type.Fun([Type.Float], Type.Bool)) !Typing.extenv;
  Typing.extenv := M.add "fispos" (Type.Fun([Type.Float], Type.Bool)) !Typing.extenv;
  Typing.extenv := M.add "fiszero" (Type.Fun([Type.Float], Type.Bool)) !Typing.extenv;
  Typing.extenv := M.add "print_char" (Type.Fun([Type.Int], Type.Unit)) !Typing.extenv;
  Typing.extenv := M.add "print_int" (Type.Fun([Type.Int], Type.Unit)) !Typing.extenv;
  Typing.extenv := M.add "read_int" (Type.Fun([Type.Unit], Type.Int)) !Typing.extenv;
  Typing.extenv := M.add "read_float" (Type.Fun([Type.Unit], Type.Float)) !Typing.extenv


let lexbuf l f = (* バッファをコンパイルしてファイルへ出力する *)
  Id.counter := 0;
  let outchan = open_out (f ^".txt") in
  let tmp0 = (Syntax.delete_unnecessary_float_func (Syntax.check_mul_and_div (Syntax.rm_lambda_abstraction (Parser.exp Lexer.token l)))) in
  let (first_hp, tmp1) = (LetGlobal.f (Typing.f tmp0)) in
    (* Syntax.print_expr tmp1 0; *)
    let tmp2 = (KNormal.f tmp1) in
      let tmp3 = (Closure.f (iter !limit (Alpha.f tmp2))) in
        let closure_string = (Closure.closureProg2String tmp3) in
        (* closureを作るまでやってファイルとして吐き出し *)
        Printf.fprintf outchan "first_hp : %s\n" (string_of_int first_hp);
        Printf.fprintf outchan "%s" closure_string;
        (close_out outchan);
        ()

let file f =
  let inchan = open_in (f ^ ".ml") in
  try
    load_ext_funcs ();
    lexbuf (Lexing.from_channel inchan) f;
    close_in inchan;
    ()
  with e -> (close_in inchan; raise e)

let () = (* ここからコンパイラの実行が開始される (caml2html: main_entry) *)
  let files = ref [] in
  Arg.parse
    [("-inline", Arg.Int(fun i -> Inline.threshold := i), "maximum size of functions inlined");
     ("-iter", Arg.Int(fun i -> limit := i), "maximum number of optimizations iterated")]
    (fun s -> files := !files @ [s])
    ("Mitou Min-Caml Compiler (C) Eijiro Sumii\n" ^
     Printf.sprintf "usage: %s [-inline m] [-iter n] ...filenames without \".ml\"..." Sys.argv.(0));
  List.iter
    (fun f -> ignore (file f))
    !files
