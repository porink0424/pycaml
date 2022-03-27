(* give names to intermediate values (K-normalization) *)

type t = (* K正規化後の式 (caml2html: knormal_t) *)
  | Unit
  | Int of int
  | Float of float
  | Neg of Id.t
  | Add of Id.t * Id.t
  | Sub of Id.t * Id.t
  | Mul of Id.t * Id.t
  | Div of Id.t * Id.t
  | FNeg of Id.t
  | FAdd of Id.t * Id.t
  | FSub of Id.t * Id.t
  | FMul of Id.t * Id.t
  | FDiv of Id.t * Id.t
  | IfEq of Id.t * Id.t * t * t (* 比較 + 分岐 *)
  | IfNEq of Id.t * Id.t * t * t (* 比較 + 分岐 *)
  | IfLE of Id.t * Id.t * t * t (* 比較 + 分岐 *)
  | IfLT of Id.t * Id.t * t * t (* 比較 + 分岐 *)
  | Let of (Id.t * Type.t) * t * t
  | Var of Id.t
  | LetRec of fundef * t
  | App of Id.t * Id.t list
  | Tuple of Id.t list
  | LetTuple of (Id.t * Type.t) list * Id.t * t
  | Get of Id.t * Id.t
  | Put of Id.t * Id.t * Id.t
  | ExtArray of Id.t
  | ExtFunApp of Id.t * Id.t list
  | ExprWithPos of t * Syntax.pos (* Oct. 14. 2021 *)
and fundef = { name : Id.t * Type.t; args : (Id.t * Type.t) list; body : t }

let rec fv = function (* 式に出現する（自由な）変数 (caml2html: knormal_fv) *)
  | Unit | Int(_) | Float(_) | ExtArray(_) -> S.empty
  | Neg(x) | FNeg(x) -> S.singleton x
  | Add(x, y) | Sub(x, y) | Mul(x, y) | Div(x, y) | FAdd(x, y) | FSub(x, y) | FMul(x, y) | FDiv(x, y) | Get(x, y) -> S.of_list [x; y]
  | IfEq(x, y, e1, e2) | IfNEq(x, y, e1, e2) | IfLE(x, y, e1, e2) | IfLT(x, y, e1, e2)  -> S.add x (S.add y (S.union (fv e1) (fv e2)))
  | Let((x, t), e1, e2) -> S.union (fv e1) (S.remove x (fv e2))
  | Var(x) -> S.singleton x
  | LetRec({ name = (x, t); args = yts; body = e1 }, e2) ->
      let zs = S.diff (fv e1) (S.of_list (List.map fst yts)) in
      S.diff (S.union zs (fv e2)) (S.singleton x)
  | App(x, ys) -> S.of_list (x :: ys)
  | Tuple(xs) | ExtFunApp(_, xs) -> S.of_list xs
  | Put(x, y, z) -> S.of_list [x; y; z]
  | LetTuple(xs, y, e) -> S.add y (S.diff (fv e) (S.of_list (List.map fst xs)))
  | ExprWithPos(x, pos) -> fv x

let rec rm_outside_pos e =
  match e with 
  | ExprWithPos(e, _) -> rm_outside_pos e 
  | _ -> e 

let insert_let (e, t) k = (* letを挿入する補助関数 (caml2html: knormal_insert) *)
  match (rm_outside_pos e) with
  | Var(x) -> k x
  | _ ->
      let x = Id.gentmp t in
      let e', t' = k x in
      Let((x, t), e, e'), t'

let rec g env = function (* K正規化ルーチン本体 (caml2html: knormal_g) *)
  | Syntax.Unit -> Unit, Type.Unit
  | Syntax.Bool(b) -> Int(if b then 1 else 0), Type.Int (* 論理値true, falseを整数1, 0に変換 (caml2html: knormal_bool) *)
  | Syntax.Int(i) -> Int(i), Type.Int
  | Syntax.Float(d) -> Float(d), Type.Float
  | Syntax.Not(e) -> g env (Syntax.If(e, Syntax.Bool(false), Syntax.Bool(true)))
  | Syntax.Neg(e) ->
      insert_let (g env e)
        (fun x -> Neg(x), Type.Int)
  | Syntax.Add(e1, e2) -> (* 足し算のK正規化 (caml2html: knormal_add) *)
      insert_let (g env e1)
        (fun x -> insert_let (g env e2)
            (fun y -> Add(x, y), Type.Int))
  | Syntax.Sub(e1, e2) ->
      insert_let (g env e1)
        (fun x -> insert_let (g env e2)
            (fun y -> Sub(x, y), Type.Int))
  | Syntax.Mul(e1, e2) ->
      insert_let (g env e1)
        (fun x -> insert_let (g env e2)
            (fun y -> Mul(x, y), Type.Int))
  | Syntax.Div(e1, e2) ->
      insert_let (g env e1)
        (fun x -> insert_let (g env e2)
            (fun y -> Div(x, y), Type.Int))
  | Syntax.FNeg(e) ->
      insert_let (g env e)
        (fun x -> FNeg(x), Type.Float)
  | Syntax.FAdd(e1, e2) ->
      insert_let (g env e1)
        (fun x -> insert_let (g env e2)
            (fun y -> FAdd(x, y), Type.Float))
  | Syntax.FSub(e1, e2) ->
      insert_let (g env e1)
        (fun x -> insert_let (g env e2)
            (fun y -> FSub(x, y), Type.Float))
  | Syntax.FMul(e1, e2) ->
      insert_let (g env e1)
        (fun x -> insert_let (g env e2)
            (fun y -> FMul(x, y), Type.Float))
  | Syntax.FDiv(e1, e2) ->
      insert_let (g env e1)
        (fun x -> insert_let (g env e2)
            (fun y -> FDiv(x, y), Type.Float))
  | Syntax.Eq _ | Syntax.NEq _ | Syntax.LE _ | Syntax.LT _ as cmp ->
      g env (Syntax.If(cmp, Syntax.Bool(true), Syntax.Bool(false)))
  | Syntax.If(comp, e3, e4) ->
    (match (Syntax.rm_outside_pos comp) with
    | Syntax.Not(e1) -> 
      (let (pos, isPosValid) = (Syntax.extract_pos comp (Syntax.Not(e1))) in
        (if isPosValid
          then (g env (Syntax.If(Syntax.ExprWithPos(e1, pos), e4, e3)))
          else (g env (Syntax.If(e1, e4, e3)))))  (* notによる分岐を変換 (caml2html: knormal_not) *)
    | Syntax.Eq(e1, e2) -> (insert_let (g env e1)
      (fun x -> insert_let (g env e2)
        (fun y ->
          let e3', t3 = g env e3 in
          let e4', t4 = g env e4 in
          IfEq(x, y, e3', e4'), t3)))
    | Syntax.NEq(e1, e2) -> (insert_let (g env e1)
      (fun x -> insert_let (g env e2)
        (fun y ->
          let e3', t3 = g env e3 in
          let e4', t4 = g env e4 in
          IfNEq(x, y, e3', e4'), t3)))
    | Syntax.LE(e1, e2) -> (insert_let (g env e1)
      (fun x -> insert_let (g env e2)
        (fun y ->
          let e3', t3 = g env e3 in
          let e4', t4 = g env e4 in
          IfLE(x, y, e3', e4'), t3)))
    | Syntax.LT(e1, e2) -> (insert_let (g env e1)
      (fun x -> insert_let (g env e2)
        (fun y ->
          let e3', t3 = g env e3 in
          let e4', t4 = g env e4 in
          IfLT(x, y, e3', e4'), t3)))
    | e1 -> 
      let (pos, isPosValid) = (Syntax.extract_pos comp e1) in
        (if isPosValid
          then (g env (Syntax.If(Syntax.Eq(Syntax.ExprWithPos(e1, pos), Syntax.ExprWithPos(Syntax.Bool(false), pos)), e4, e3)))
          else (g env (Syntax.If(Syntax.Eq(e1, Syntax.Bool(false)), e4, e3))))  (* 比較のない分岐を変換 (caml2html: knormal_if) *))
  | Syntax.Let((x, t), e1, e2) ->
      let e1', t1 = g env e1 in
      let e2', t2 = g (M.add x t env) e2 in
      Let((x, t), e1', e2'), t2
  | Syntax.Var(x) when M.mem x env -> Var(x), M.find x env
  | Syntax.Var(x) -> (* 外部配列の参照 (caml2html: knormal_extarray) *)
      (match M.find x !Typing.extenv with
      | Type.Array(_) as t -> ExtArray x, t
      | _ -> failwith (Printf.sprintf "external variable %s does not have an array type" x))
  | Syntax.LetRec({ Syntax.name = (x, t); Syntax.args = yts; Syntax.body = e1 }, e2) ->
      let env' = M.add x t env in
      let e2', t2 = g env' e2 in
      let e1', t1 = g (M.add_list yts env') e1 in
      LetRec({ name = (x, t); args = yts; body = e1' }, e2'), t2
  | Syntax.App(syntax_var, e2s) when (
      match (Syntax.rm_outside_pos syntax_var) with
      | Syntax.Var(f) -> (not (M.mem f env))
      | _ -> false
  ) ->(match (Syntax.rm_outside_pos syntax_var) with 
      | Syntax.Var(f) ->
      (match M.find f !Typing.extenv with
      | Type.Fun(_, t) ->
          let rec bind xs = function (* "xs" are identifiers for the arguments *)
            | [] -> 
              let (pos, isPosValid) = (Syntax.extract_pos syntax_var (Syntax.Var(f))) in
              (if isPosValid
                then ExprWithPos(ExtFunApp(f, xs), pos), t
                else ExtFunApp(f, xs), t)
            | e2 :: e2s ->
                insert_let (g env e2)
                  (fun x -> bind (xs @ [x]) e2s) in
          bind [] e2s (* left-to-right evaluation *)
      | _ -> assert false)
      | _ -> assert false)
  | Syntax.App(e1, e2s) ->
      (match g env e1 with
      | _, Type.Fun(_, t) as g_e1 ->
          insert_let g_e1
            (fun f ->
              let rec bind xs = function (* "xs" are identifiers for the arguments *)
                | [] -> App(f, xs), t
                | e2 :: e2s ->
                    insert_let (g env e2)
                      (fun x -> bind (xs @ [x]) e2s) in
              bind [] e2s) (* left-to-right evaluation *)
      | _ -> assert false)
  | Syntax.Tuple(es) ->
      let rec bind xs ts = function (* "xs" and "ts" are identifiers and types for the elements *)
        | [] -> Tuple(xs), Type.Tuple(ts)
        | e :: es ->
            let _, t as g_e = g env e in
            insert_let g_e
              (fun x -> bind (xs @ [x]) (ts @ [t]) es) in
      bind [] [] es
  | Syntax.LetTuple(xts, e1, e2) ->
      insert_let (g env e1)
        (fun y ->
          let e2', t2 = g (M.add_list xts env) e2 in
          LetTuple(xts, y, e2'), t2)
  | Syntax.Array(e1, e2) ->
      insert_let (g env e1)
        (fun x ->
          let _, t2 as g_e2 = g env e2 in
          insert_let g_e2
            (fun y ->
              let l =
                match t2 with
                | Type.Float -> "create_float_array"
                | _ -> "create_array" in
              ExtFunApp(l, [x; y]), Type.Array(t2)))
  | Syntax.Get(e1, e2) ->
      (match g env e1 with
      |        _, Type.Array(t) as g_e1 ->
          insert_let g_e1
            (fun x -> insert_let (g env e2)
                (fun y -> Get(x, y), t))
      | _, Type.Int ->
        insert_let (g env e1)
          (fun x -> insert_let (g env e2)
              (fun y -> Get(x, y), Type.Int))
      | _ -> assert false)
  | Syntax.Put(e1, e2, e3) ->
      insert_let (g env e1)
        (fun x -> insert_let (g env e2)
            (fun y -> insert_let (g env e3)
                (fun z -> Put(x, y, z), Type.Unit)))
  | Syntax.ExprWithPos(e, p) ->
      let tmp = g env e in
      ExprWithPos((fst tmp), p), (snd tmp)
  | _ -> failwith "g env k-normal"



(* print functions *)
let rec indentn n =
  if (n <= 0) 
    then () 
    else (print_string "  "; indentn (n-1)) (* インデント幅はここで調整 *)

let rec print_knormal k n =
  match k with
  | Unit -> 
      print_string "()"
  | Int i ->
      print_int i
  | Float f ->
      print_float f
  | Neg a ->
      (print_string "iNeg(";
       Id.print_id a;
       print_string ")")
  | Add (a,b) ->
      (print_string "iAdd(";
       Id.print_id a;
       print_string ",";
       Id.print_id b;
       print_string ")")
  | Sub (a,b) ->
      (print_string "iSub(";
       Id.print_id a;
       print_string ",";
       Id.print_id b;
       print_string ")")
  | Mul (a,b) ->
      (print_string "iMul(";
       Id.print_id a;
       print_string ",";
       Id.print_id b;
       print_string ")")
  | Div (a,b) ->
      (print_string "iDiv(";
       Id.print_id a;
       print_string ",";
       Id.print_id b;
       print_string ")")
  | FNeg a ->
      (print_string "FNeg(";
       Id.print_id a;
       print_string ")")
  | FAdd (a,b) ->
      (print_string "FAdd(";
       Id.print_id a;
       print_string ",";
       Id.print_id b;
       print_string ")")
  | FSub (a,b) ->
      (print_string "FSub(";
       Id.print_id a;
       print_string ",";
       Id.print_id b;
       print_string ")")
  | FMul (a,b) ->
      (print_string "FMul(";
       Id.print_id a;
       print_string ",";
       Id.print_id b;
       print_string ")")
  | FDiv (a,b) ->
      (print_string "FDiv(";
       Id.print_id a;
       print_string ",";
       Id.print_id b;
       print_string ")")
  | IfEq (a,b,c,d) ->
      (print_string "\n";
       indentn (n+1);
       print_string "IfEq(\n";
       indentn (n+2);
       Id.print_id a;
       print_string " == ";
       Id.print_id b;
       print_string ", \n";
       indentn (n+2);
       print_knormal c (n+2);
       print_string ", \n";
       indentn (n+2);
       print_knormal d (n+2);
       print_string "\n";
       indentn (n+1);
       print_string ")\n";
       indentn n)
  | IfNEq (a,b,c,d) ->
      (print_string "\n";
       indentn (n+1);
       print_string "IfNEq(\n";
       indentn (n+2);
       Id.print_id a;
       print_string " == ";
       Id.print_id b;
       print_string ", \n";
       indentn (n+2);
       print_knormal c (n+2);
       print_string ", \n";
       indentn (n+2);
       print_knormal d (n+2);
       print_string "\n";
       indentn (n+1);
       print_string ")\n";
       indentn n)
  | IfLE (a,b,c,d) ->
      (print_string "\n";
      indentn (n+1);
      print_string "IfLE(\n";
      indentn (n+2);
      Id.print_id a;
      print_string " <= ";
      Id.print_id b;
      print_string ", \n";
      indentn (n+2);
      print_knormal c (n+2);
      print_string ", \n";
      indentn (n+2);
      print_knormal d (n+2);
      print_string "\n";
      indentn (n+1);
      print_string ")\n";
      indentn n)
  | IfLT (a,b,c,d) ->
      (print_string "\n";
      indentn (n+1);
      print_string "IfLT(\n";
      indentn (n+2);
      Id.print_id a;
      print_string " <= ";
      Id.print_id b;
      print_string ", \n";
      indentn (n+2);
      print_knormal c (n+2);
      print_string ", \n";
      indentn (n+2);
      print_knormal d (n+2);
      print_string "\n";
      indentn (n+1);
      print_string ")\n";
      indentn n)
  | Let (a,b,c) ->
      (print_string "\n";
        indentn (n+1);
        print_string "Let(";
        print_knormal_fundef_arg [a] false;
        print_string ", \n";
        indentn (n+2);
        print_knormal b (n+2);
        print_string ", \n";
        indentn (n+2);
        print_knormal c (n+2);
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
      print_knormal_fundef a (n+2);
      print_string ", \n";
      indentn (n+2);
      print_knormal b (n+2);
      print_string "\n";
      indentn (n+1);
      print_string ")\n";
      indentn n)
  | App (a,b) ->
      (print_string "App(";
       Id.print_id a;
       print_string ", ";
       print_knormal_list b false;
       print_string ")")
  | Tuple a ->
      print_knormal_list a false
  | LetTuple (a,b,c) ->
      (print_string "\n";
        indentn (n+1);
        print_string "LetTuple(\n";
        indentn (n+2);
        print_string "[";
        print_knormal_fundef_arg a false;
        print_string "], \n";
        indentn (n+2);
        Id.print_id b;
        print_string ", \n";
        indentn (n+2);
        print_knormal c (n+2);
        print_string "\n";
        indentn (n+1);
        print_string ")\n";
        indentn n)
  | Get (a,b) ->
      (print_string "Get(";
       Id.print_id a;
       print_string ", ";
       Id.print_id b;
       print_string ")")
  | Put (a,b,c) ->
      (print_string "Put(";
       Id.print_id a;
       print_string ", ";
       Id.print_id b;
       print_string ", ";
       Id.print_id c;
       print_string ")")
  | ExtArray a ->
      (print_string "ExtArray(";
       Id.print_id a;
       print_string ")")
  | ExtFunApp (a,b) ->
      (print_string "ExtFunApp(";
       Id.print_id a;
       print_string ", ";
       print_knormal_list b false;
       print_string ")")
  | ExprWithPos (a,p) ->
      (print_string "\n";
        indentn (n+1);
        print_string "ExprWithPos(\n";
        indentn (n+2);
        print_knormal a (n+2);
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
and print_knormal_list l flg = 
  match l with
  | [] -> print_string "]"
  | x::rest -> 
    (if flg then print_string "; " else print_string "["; (* １つ目なら"["，２つ目以降なら";"を表示 *)
     (* print_knormal x; *)
     Id.print_id x;
     print_knormal_list rest true)
and print_knormal_fundef_arg args flg =
  match args with
  | [] -> print_string ""
  | (id,ty)::rest ->
      (if flg then print_string "; "; (* ２つ目以降なら";"を表示 *)
       print_string "(";
       Id.print_id id;
       print_string ":";
       Type.print_type ty;
       print_string ")";
       print_knormal_fundef_arg rest true)
and print_knormal_fundef f n =
  print_string "(";
  print_knormal_fundef_arg [f.name] false;
  print_string ", [";
  print_knormal_fundef_arg f.args false;
  print_string "], ";
  print_knormal f.body n;
  print_string ")"

(* remove common parts *)
let print_fv fv =
  print_string "{";
  S.iter Id.print_id fv;
  print_string "}"
let print_dict d =
  print_endline "------------- dict -----------------";
  let rec inner d =
    match d with
    | [] -> ()
    | (a, b) :: [] -> (
      print_string "(";
      print_knormal a 0;
      print_string ", ";
      print_knormal b 0;
      print_string " <- ";
      print_fv (fv a);
      print_string ")")
    | (a, b) :: tail -> (
      print_string "(";
      print_knormal a 0;
      print_string ", ";
      print_knormal b 0;
      print_string " <- ";
      print_fv (fv a);
      print_string ")";
      print_string "; ";
      inner tail)
  in
  print_string "[";
  inner d;
  print_endline "]"
let rec rm_pos k =
  match k with
  | IfEq (a, b, c, d) -> IfEq (a, b, rm_pos c, rm_pos d)
  | IfNEq (a, b, c, d) -> IfNEq (a, b, rm_pos c, rm_pos d)
  | IfLE (a, b, c, d) -> IfLE (a, b, rm_pos c, rm_pos d)
  | IfLT (a, b, c, d) -> IfLT (a, b, rm_pos c, rm_pos d)
  | Let (a, b, c) -> Let (a, rm_pos b, rm_pos c)
  | LetRec (a, b) -> LetRec (a, rm_pos b)
  | LetTuple (a, b, c) -> LetTuple (a, b, rm_pos c)
  | ExprWithPos (a, _) -> rm_pos a
  | _ -> k
and rm_affected vars symbols =
  match vars with
  | [] -> symbols
  | v :: tail -> rm_affected tail @@ List.filter (fun (a, b) -> not @@ S.mem v (fv a)) symbols
and rm_common k =
  let rec inner k symbols =
    (*print_dict symbols;*)
    match List.assoc_opt (rm_pos k) symbols with
    | Some e -> e
    | None -> (
      match k with
      (* constant-like *)
      | Unit | Int _ | Float _
      | Neg _ | FNeg _ | Var _
      | Tuple _ | Get (_, _) | ExtArray _ -> k
      (* arith *)
      | Add (a, b) | Sub (a, b)
      | Mul (a, b) | Div (a, b)
      | FAdd (a, b) | FSub (a, b)
      | FMul (a, b) | FDiv (a, b) -> k
      (* potential side-effects *)
      | App (_, _) 
      | Put (_, _, _)
      | ExtFunApp (_, _) -> k
      (* if statement *)
      | IfEq (a, b, c, d) -> IfEq (a, b, inner c symbols, inner d symbols)
      | IfNEq (a, b, c, d) -> IfNEq (a, b, inner c symbols, inner d symbols)
      | IfLE (a, b, c, d) -> IfLE (a, b, inner c symbols, inner d symbols)
      | IfLT (a, b, c, d) -> IfLT (a, b, inner c symbols, inner d symbols)
      (* let statement *)
      | Let ((a, b), c, d) -> (
        (* substitute c with existing symbol pairs *)
        let c' = inner c symbols in
        (* no changle implies new symbol pair *)
        let symbols' =
          if (rm_pos c) = (rm_pos c') then
            ((rm_pos c, Var a) :: symbols)
          else
            symbols
        in
        (* remove symbol pairs containing affected variables *)
        let symbols'' = rm_affected [a] symbols' in
        Let ((a, b), c', inner d symbols''))
      (* unpack tuple + funtion definitoin *)
      | LetTuple (a, b, c) -> LetTuple (a, b, inner c symbols)
      | LetRec (a, b) -> LetRec (a, inner b symbols)
      (* something else *)
      | ExprWithPos (a, p) -> ExprWithPos (inner a symbols, p))
  in
  inner k []


let f e = fst (g M.empty e)