
type pos = int * int (* line * offset *)
type t = (* MinCamlの構文を表現するデータ型 (caml2html: syntax_t) *)
  | Unit
  | Bool of bool
  | Int of int
  | Float of float
  | Not of t
  | Neg of t
  | Add of t * t
  | Sub of t * t
  | Mul of t * t
  | Div of t * t
  | FNeg of t
  | FAdd of t * t
  | FSub of t * t
  | FMul of t * t
  | FDiv of t * t
  | Eq of t * t
  | NEq of t * t
  | LE of t * t
  | LT of t * t
  | If of t * t * t
  | Let of (Id.t * Type.t) * t * t
  | Var of Id.t
  | LetRec of fundef * t
  | LetGlobal of (Id.t * Type.t) * t * t
  | App of t * t list
  | Tuple of t list
  | LetTuple of (Id.t * Type.t) list * t * t
  | Array of t * t
  | Get of t * t
  | Put of t * t * t
  | ExprWithPos of t * pos
  | Fun of t list * t
and fundef = { name : Id.t * Type.t; args : (Id.t * Type.t) list; body : t }

let rec rm_outside_pos e = 
  match e with 
  | ExprWithPos(e, _) -> rm_outside_pos e 
  | _ -> e 

(* print functions *)
let rec indentn n =
  if (n <= 0) 
    then () 
    else (print_string "  "; indentn (n-1)) (* インデント幅はここで調整 *)


let rec print_expr e n =
  match e with
  | Unit -> 
      print_string "()"
  | Bool b ->
      if b then
        print_string "true"
      else 
        print_string "false"
  | Int i ->
      print_int i
  | Float f ->
      print_float f
  | Not t ->
      (print_string "not ";
        print_expr t n)
  | Neg t ->
      (print_string "iNeg(";
        print_expr t n;
        print_string ")")
  | Add (a,b) ->
      (print_string "iAdd(";
        print_expr a n;
        print_string ", ";
        print_expr b n;
        print_string ")")
  | Sub (a,b) ->
      (print_string "iSub(";
        print_expr a n;
        print_string ", ";
        print_expr b n;
        print_string ")")
  | Mul (a,b) ->
      (print_string "iMul(";
        print_expr a n;
        print_string ", ";
        print_expr b n;
        print_string ")")
  | Div (a,b) ->
      (print_string "iDiv(";
        print_expr a n;
        print_string ", ";
        print_expr b n;
        print_string ")")
  | FNeg t ->
      (print_string "FNeg(";
        print_expr t n;
        print_string ")")
  | FAdd (a,b) ->
      (print_string "FAdd(";
        print_expr a n;
        print_string ", ";
        print_expr b n;
        print_string ")")
  | FSub (a,b) ->
      (print_string "FSub(";
        print_expr a n;
        print_string ", ";
        print_expr b n;
        print_string ")")
  | FMul (a,b) ->
      (print_string "FMul(";
        print_expr a n;
        print_string ", ";
        print_expr b n;
        print_string ")")
  | FDiv (a,b) ->
      (print_string "FDiv(";
        print_expr a n;
        print_string ", ";
        print_expr b n;
        print_string ")")
  | Eq (a,b) ->
      (print_string "Eq(";
        print_expr a n;
        print_string ", ";
        print_expr b n;
        print_string ")")
  | NEq (a,b) ->
      (print_string "NEq(";
        print_expr a n;
        print_string ", ";
        print_expr b n;
        print_string ")")
  | LE (a,b) ->
      (print_string "LE(";
        print_expr a n;
        print_string ", ";
        print_expr b n;
        print_string ")")
  | LT (a,b) ->
      (print_string "LT(";
        print_expr a n;
        print_string ", ";
        print_expr b n;
        print_string ")")
  | If (a,b,c) ->
      (print_string "\n";
        indentn (n+1);
        print_string "If(";
        print_expr a (n+1);
        print_string ", \n";
        indentn (n+2);
        print_expr b (n+2);
        print_string ", \n";
        indentn (n+2);
        print_expr c (n+2);
        print_string ")")
  | Let (a,b,c) ->
      (print_string "\n";
        indentn (n+1);
        print_string "Let(";
        print_fundef_arg [a] false;
        print_string ", \n";
        indentn (n+2);
        print_expr b (n+2);
        print_string ", \n";
        indentn (n+2);
        print_expr c (n+2);
        print_string "\n";
        indentn (n+1);
        print_string ")\n";
        indentn n)
  | Var a ->
      (print_string "Var(";
        Id.print_id a;
        print_string ")")
  | LetRec (a,b) ->
      (print_string "\n";
        indentn (n+1);
        print_string "LetRec(\n";
        indentn (n+2);
        print_fundef a (n+2);
        print_string ", \n";
        indentn (n+2);
        print_expr b (n+2);
        print_string "\n";
        indentn (n+1);
        print_string ")\n";
        indentn n)
  | LetGlobal (a,b,c) ->
      (print_string "\n";
        indentn (n+1);
        print_string "LetGlobal(";
        print_fundef_arg [a] false;
        print_string ", \n";
        indentn (n+2);
        print_expr b (n+2);
        print_string ", \n";
        indentn (n+2);
        print_expr c (n+2);
        print_string "\n";
        indentn (n+1);
        print_string ")\n";
        indentn n)
  | App (a,b) ->
      (print_string "App(";
        print_expr a n;
        print_string ", ";
        print_expr_list b false n;
        print_string ")")
  | Tuple a ->
      print_expr_list a false n
  | LetTuple (a,b,c) ->
      (print_string "\n";
        indentn (n+1);
        print_string "LetTuple(\n";
        indentn (n+2);
        print_string "[";
        print_fundef_arg a false;
        print_string "], \n";
        indentn (n+2);
        print_expr b (n+2);
        print_string ", \n";
        indentn (n+2);
        print_expr c (n+2);
        print_string "\n";
        indentn (n+1);
        print_string ")\n";
        indentn n)
  | Array (a,b) ->
      (print_string "Array(";
        print_expr a n;
        print_string ", ";
        print_expr b n;
        print_string ")")
  | Get (a,b) ->
      (print_string "Get(";
        print_expr a n;
        print_string ", ";
        print_expr b n;
        print_string ")")
  | Put (a,b,c) ->
      (print_string "Put(";
        print_expr a n;
        print_string ", ";
        print_expr b n;
        print_string ", ";
        print_expr c n;
        print_string ")")
  | ExprWithPos (a,p) ->
      (print_string "\n";
        indentn (n+1);
        print_string "ExprWithPos(\n";
        indentn (n+2);
        print_expr a (n+2);
        print_string "\n";
        indentn (n+2);
        print_string "Pos(";
          print_int (fst p);
          print_string ",";
          print_int (snd p);
          print_string ")\n";
        indentn (n+1);
        print_string ")\n";
        indentn (n))
  | Fun (x_list, t) ->
    print_string ("Fun(");
    List.map (fun x -> print_expr x) x_list;
    print_string  (", ");
    print_expr t n;
    print_string (")");

and print_expr_list l flg n = 
  match l with
  | [] -> print_string "]"
  | x::rest -> 
    (if flg then print_string "; " else print_string "["; (* １つ目なら"["，２つ目以降なら";"を表示 *)
      print_expr x n;
      print_expr_list rest true n)
and print_fundef_arg args flg = (* print_list と分けた意味はあまりない。多少早くなるかも？… *)
  match args with
  | [] -> print_string ""
  | (id,ty)::rest ->
      (if flg then print_string "; "; (* ２つ目以降なら";"を表示 *)
        print_string "(";
        Id.print_id id;
        print_string ":";
        Type.print_type ty;
        print_string ")";
        print_fundef_arg rest true)
and print_fundef f n =
  print_string "(";
  print_fundef_arg [f.name] false;
  print_string ", [";
  print_fundef_arg f.args false;
  print_string "], ";
  print_expr f.body n;
  print_string ")"
  


let rec extract_pos e target_e =
  match e with
  | ExprWithPos(next_e, pos) when (next_e = target_e) -> pos, true
  | ExprWithPos(next_e, pos) -> extract_pos next_e target_e
  | _ -> (0,0), false



 (*λ抽象，部分適用の実装*)

let env = ref [] (*関数名から，その関数の引数を返す環境 見つからなかったときfalseを返す*)

let rec env_find f_name env =
  match env with
  | (f, args_list) :: res  -> if f_name = f then (true, args_list) else (env_find f_name res)
  | [] -> (false, [])
  | _ -> failwith "env not found."

let env_add f_name args_list env =
  let list = List.map (fun (x, t) -> Var(x)) args_list in
  (f_name, list) :: env

let rec list_slice list len = (*listの後ろからlen個分を切り出す*)
  if (List.length list) = len
    then list
  else match list with
    | item :: res -> (list_slice res len)
    | _ -> failwith("match error in syntax")
  
(* 与えられた数が2の何乗かを返す関数。2の冪乗でなければ-1を返す *)
let rec log_int_2_loop n prod ans =
  if n = prod then ans else if prod > n then -1 else (log_int_2_loop n (prod * 2) (ans + 1))

let rec log_int_2 n = (log_int_2_loop n 1 0)

(* 整数の掛け算、割り算は2の冪乗のみ許す。以下の関数は第二引数が2の冪乗になっているかをチェックし、大丈夫であればそのlog_2をとる *)
let rec check_mul_and_div e =
  match e with
  | Mul(e1, e2) ->
    (match (rm_outside_pos e2) with
    | Int n when ((log_int_2 n) >= 0) -> Mul((check_mul_and_div e1), (Int(log_int_2 n)))
    | _ -> failwith("Invalid Mul."))
  | Div(e1, e2) ->
    (match (rm_outside_pos e2) with
    | Int n when ((log_int_2 n) >= 0) -> Div((check_mul_and_div e1), (Int(log_int_2 n)))
    | _ -> failwith("Invalid Div."))
  | Not(e) -> Not(check_mul_and_div e)
  | Neg(e) -> Neg(check_mul_and_div e)
  | Add(e1, e2) -> Add((check_mul_and_div e1), (check_mul_and_div e2))
  | Sub(e1, e2) -> Sub((check_mul_and_div e1), (check_mul_and_div e2))
  | FNeg(e) -> FNeg(check_mul_and_div e)
  | FAdd(e1, e2) -> FAdd((check_mul_and_div e1), (check_mul_and_div e2))
  | FSub(e1, e2) -> FSub((check_mul_and_div e1), (check_mul_and_div e2))
  | FMul(e1, e2) -> FMul((check_mul_and_div e1), (check_mul_and_div e2))
  | FDiv(e1, e2) -> FDiv((check_mul_and_div e1), (check_mul_and_div e2))
  | Eq(e1, e2) -> Eq((check_mul_and_div e1), (check_mul_and_div e2))
  | NEq(e1, e2) -> NEq((check_mul_and_div e1), (check_mul_and_div e2))
  | LE(e1, e2) -> LE((check_mul_and_div e1), (check_mul_and_div e2))
  | LT(e1, e2) -> LT((check_mul_and_div e1), (check_mul_and_div e2))
  | If(e1, e2, e3) -> If((check_mul_and_div e1), (check_mul_and_div e2), (check_mul_and_div e3))
  | Let((x,t), e1, e2) -> Let((x,t), (check_mul_and_div e1), (check_mul_and_div e2))
  | LetGlobal((x,t), e1, e2) -> LetGlobal((x,t), (check_mul_and_div e1), (check_mul_and_div e2))
  | LetRec({ name = xt; args = yts; body = e1 }, e2) ->
    LetRec({ name = xt;
             args = yts;
             body = check_mul_and_div e1 },
           check_mul_and_div e2)
  | App(e, es) -> App(check_mul_and_div e, List.map check_mul_and_div es)
  | Tuple(es) -> Tuple(List.map check_mul_and_div es)
  | LetTuple(xts, e1, e2) -> LetTuple(xts, check_mul_and_div e1, check_mul_and_div e2)
  | Array(e1, e2) -> Array(check_mul_and_div e1, check_mul_and_div e2)
  | Get(e1, e2) -> Get(check_mul_and_div e1, check_mul_and_div e2)
  | Put(e1, e2, e3) -> Put(check_mul_and_div e1, check_mul_and_div e2, check_mul_and_div e3)
  | ExprWithPos(e, p) -> ExprWithPos(check_mul_and_div e, p)
  | e -> e

(* λ抽象を除去する *)
let rec rm_lambda_abstraction e =
  match e with
  | Not(e) -> Not(rm_lambda_abstraction e)
  | Neg(e) -> Neg(rm_lambda_abstraction e)
  | Add(e1, e2) -> Add((rm_lambda_abstraction e1), (rm_lambda_abstraction e2))
  | Sub(e1, e2) -> Sub((rm_lambda_abstraction e1), (rm_lambda_abstraction e2))
  | Mul(e1, e2) -> Mul((rm_lambda_abstraction e1), (rm_lambda_abstraction e2))
  | Div(e1, e2) -> Div((rm_lambda_abstraction e1), (rm_lambda_abstraction e2))
  | FNeg(e) -> FNeg(rm_lambda_abstraction e)
  | FAdd(e1, e2) -> FAdd((rm_lambda_abstraction e1), (rm_lambda_abstraction e2))
  | FSub(e1, e2) -> FSub((rm_lambda_abstraction e1), (rm_lambda_abstraction e2))
  | FMul(e1, e2) -> FMul((rm_lambda_abstraction e1), (rm_lambda_abstraction e2))
  | FDiv(e1, e2) -> FDiv((rm_lambda_abstraction e1), (rm_lambda_abstraction e2))
  | Eq(e1, e2) -> Eq((rm_lambda_abstraction e1), (rm_lambda_abstraction e2))
  | NEq(e1, e2) -> NEq((rm_lambda_abstraction e1), (rm_lambda_abstraction e2))
  | LE(e1, e2) -> LE((rm_lambda_abstraction e1), (rm_lambda_abstraction e2))
  | LT(e1, e2) -> LT((rm_lambda_abstraction e1), (rm_lambda_abstraction e2))
  | If(e1, e2, e3) -> If((rm_lambda_abstraction e1), (rm_lambda_abstraction e2), (rm_lambda_abstraction e3))
  | Let((x,t), e1, e2) -> Let((x,t), (rm_lambda_abstraction e1), (rm_lambda_abstraction e2))
  | LetGlobal((x,t), e1, e2) -> LetGlobal((x,t), (rm_lambda_abstraction e1), (rm_lambda_abstraction e2))
  | LetRec(fundef, e) -> 
    let f_name = (fst fundef.name) in
    env := (env_add f_name fundef.args !env);
    LetRec(fundef, (rm_lambda_abstraction e))
  | App(e, e_list) ->
    let e' = (rm_lambda_abstraction e) in
    let e_list' = (List.map rm_lambda_abstraction e_list) in
    (match (rm_outside_pos e') with
    | If(e1, e2, e3) -> (
      let e1' = (rm_lambda_abstraction e1) in
      (If(e1', (rm_lambda_abstraction (App(e2, e_list'))), (rm_lambda_abstraction (App(e3, e_list'))))))
    | Let((x,t), e1, e2) -> Let((x,t), (rm_lambda_abstraction e1), (rm_lambda_abstraction (App(e2, e_list'))))
    | LetRec(fundef, e) ->
      let f_name = (fst fundef.name) in
      env := (env_add f_name fundef.args !env);
      LetRec(fundef, (rm_lambda_abstraction (App(e, e_list'))))
    | LetTuple(lis, e1, e2) -> LetTuple(lis, (rm_lambda_abstraction e1), (rm_lambda_abstraction (App(e2, e_list'))))
    | Fun(x_list, e) -> (rm_lambda_abstraction (App((rm_lambda_abstraction e'), e_list')))
    | Var(f) -> (
      let len = (List.length e_list') in
      (match (env_find f !env) with
      | (true, args_list) when ((List.length args_list) = len) -> App(e', e_list') (*環境に登録した引数のカウントと一致する場合はそのまま*)
      | (true, args_list) -> let other_args_list = (list_slice args_list ((List.length args_list) - len)) in (rm_lambda_abstraction (Fun(other_args_list, App(Var(f), (e_list'@other_args_list))))) (*部分適用*)
      | (false, _) -> App(e', e_list')))  (*環境で見つからなかった場合は，外部関数かsyntax errorなのでそのまま*)
    | App(e1, e1_list) -> (App((App((rm_lambda_abstraction e1), (List.map rm_lambda_abstraction e1_list))), e_list'))
    | _ -> failwith("error"))
  | LetTuple(lis, e1, e2) -> LetTuple(lis, (rm_lambda_abstraction e1), (rm_lambda_abstraction e2))
  | Array(e1, e2) -> Array((rm_lambda_abstraction e1), (rm_lambda_abstraction e2))
  | Get(e1, e2) -> Get((rm_lambda_abstraction e1), (rm_lambda_abstraction e2))
  | Put(e1, e2, e3) -> Put((rm_lambda_abstraction e1), (rm_lambda_abstraction e2), (rm_lambda_abstraction e3))
  | ExprWithPos(e, pos) -> ExprWithPos(rm_lambda_abstraction e, pos)
  | Fun(x_list, e) ->
    let f_name = Id.genid "LambdaF" in
    let f_type = Type.gentyp () in
    let fundef = { name = (f_name, f_type); args = (List.map (fun (Var(x)) -> (x, Type.gentyp ())) x_list); body = e } in
    LetRec(fundef, Var(f_name))
  | e -> e



(* if fless () () then ... else ... の中のflessなど，if内の小数関係の冗長な関数を消去する *)
let rec delete_unnecessary_float_func = function
  | Not(e) -> Not(delete_unnecessary_float_func e)
  | Neg(e) -> Neg(delete_unnecessary_float_func e)
  | Add(e1, e2) -> Add((delete_unnecessary_float_func e1), (delete_unnecessary_float_func e2))
  | Sub(e1, e2) -> Sub((delete_unnecessary_float_func e1), (delete_unnecessary_float_func e2))
  | Mul(e1, e2) -> Mul((delete_unnecessary_float_func e1), (delete_unnecessary_float_func e2))
  | Div(e1, e2) -> Div((delete_unnecessary_float_func e1), (delete_unnecessary_float_func e2))
  | FNeg(e) -> FNeg(delete_unnecessary_float_func e)
  | FAdd(e1, e2) -> FAdd((delete_unnecessary_float_func e1), (delete_unnecessary_float_func e2))
  | FSub(e1, e2) -> FSub((delete_unnecessary_float_func e1), (delete_unnecessary_float_func e2))
  | FMul(e1, e2) -> FMul((delete_unnecessary_float_func e1), (delete_unnecessary_float_func e2))
  | FDiv(e1, e2) -> FDiv((delete_unnecessary_float_func e1), (delete_unnecessary_float_func e2))
  | Eq(e1, e2) -> Eq((delete_unnecessary_float_func e1), (delete_unnecessary_float_func e2))
  | NEq(e1, e2) -> NEq((delete_unnecessary_float_func e1), (delete_unnecessary_float_func e2))
  | LE(e1, e2) -> LE((delete_unnecessary_float_func e1), (delete_unnecessary_float_func e2))
  | LT(e1, e2) -> LT((delete_unnecessary_float_func e1), (delete_unnecessary_float_func e2))

  (* fless *)
  | If((App((Var("fless")), (e_arg1 :: (e_arg2 :: [])))), e2, e3) ->
    If((LE(e_arg1, e_arg2)), (delete_unnecessary_float_func e2), (delete_unnecessary_float_func e3))
  (* fisneg *)
  | If((App((Var("fisneg")), (e_arg1 :: []))), e2, e3) ->
    If((Not(LE((Float(0.0)), e_arg1))), (delete_unnecessary_float_func e2), (delete_unnecessary_float_func e3))
  (* fispos *)
  | If((App((Var("fispos")), (e_arg1 :: []))), e2, e3) ->
    If((Not(LE(e_arg1, (Float(0.0))))), (delete_unnecessary_float_func e2), (delete_unnecessary_float_func e3))
  (* fiszero *)
  | If((App((Var("fiszero")), (e_arg1 :: []))), e2, e3) ->
    If((Eq(e_arg1, (Float(0.0)))), (delete_unnecessary_float_func e2), (delete_unnecessary_float_func e3))

  | If(e1, e2, e3) -> If((delete_unnecessary_float_func e1), (delete_unnecessary_float_func e2), (delete_unnecessary_float_func e3))
  | Let((x,t), e1, e2) -> Let((x,t), (delete_unnecessary_float_func e1), (delete_unnecessary_float_func e2))
  | LetGlobal((x,t), e1, e2) -> LetGlobal((x,t), (delete_unnecessary_float_func e1), (delete_unnecessary_float_func e2))
  | LetRec({ name = xt; args = yts; body = e1 }, e2) ->
    LetRec({ name = xt;
             args = yts;
             body = delete_unnecessary_float_func e1 },
             delete_unnecessary_float_func e2)
  | App(e, es) -> App(delete_unnecessary_float_func e, List.map delete_unnecessary_float_func es)
  | LetTuple(lis, e1, e2) -> LetTuple(lis, (delete_unnecessary_float_func e1), (delete_unnecessary_float_func e2))
  | Array(e1, e2) -> Array((delete_unnecessary_float_func e1), (delete_unnecessary_float_func e2))
  | Get(e1, e2) -> Get((delete_unnecessary_float_func e1), (delete_unnecessary_float_func e2))
  | Put(e1, e2, e3) -> Put((delete_unnecessary_float_func e1), (delete_unnecessary_float_func e2), (delete_unnecessary_float_func e3))
  | ExprWithPos(e, pos) -> ExprWithPos(delete_unnecessary_float_func e, pos)
  | e -> e
