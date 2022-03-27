(* globalな配列変数のヒープ上のアドレスを確定させる *)

open Syntax

(* globalな配列変数のヒープ上のアドレスを格納する *)
let globalenv = ref []

(* グローバル配列のアドレスを全ての関数に教えてあげる必要があるので、そのLet文をpreletsに形成。関数内で使われないアドレスはのちに不要定義削除で消されるので最初は全て挿入しておく *)
let prelets = ref []

let hp = ref 4

let rec print_globalenv lis outchan count =
  match lis with
  | [] -> ()
  | (x, hp, t, e1_array, n) :: res -> 
    Printf.fprintf outchan "%s" ("globalenv_" ^ (string_of_int count) ^ " : ");
    Printf.fprintf outchan "%s," x;
    Printf.fprintf outchan "%s," (string_of_int hp);
    Printf.fprintf outchan "%s," (Type.type2string t);
    Printf.fprintf outchan "%s\n" (string_of_int n);
    print_globalenv res outchan (count + 1) 

(* global変数をヒープ上に作るためのPutを挿入する補助関数 *)
let rec insert_put exp n p =
  if n <= 0 then Unit
  else 
    (let put = Put(Int(p), Int(0), exp) in
    Let((Id.gentmp Type.Unit, Type.Unit), put, (insert_put exp (n-1) (p + 4))))

let rec find x lis =
  match lis with
  | [] -> failwith "find error."
  | (x1, hp1, _, _, _) :: res -> if x1 = x then hp1 else find x res

let rec mem x lis =
  match lis with
  | [] -> false
  | (x1, _, _, _, _) :: res -> if x1 = x then true else mem x res

(* globalな配列変数のヒープ上のアドレスを確定させ、envに書き加えて、putをinsertしていく *)
let rec decide_address exp =
  match exp with
  | LetGlobal((x,(Type.Array(t))),e1,e2) -> (
      match e1 with
      | Array(Int(n), e1_array) -> 
        globalenv := ((x, (!hp), t, e1_array, n) :: !globalenv);
        let tmp_hp = !hp in
        hp := !hp + 4 * n;
        let tmp = (Id.gentmp t) in
        prelets := (x, Int(tmp_hp), t) :: !prelets;
        Let((tmp, t), e1_array, Let(((Id.gentmp Type.Unit), Type.Unit), (insert_put (Var(tmp)) n tmp_hp), decide_address e2))
      | _ -> failwith "A global variable is allowed only for Array.")
  | Let(xt, e1, e2) -> Let(xt, e1, (decide_address e2))
  | LetRec({ name = xt; args = yts; body = e1 }, e2) -> LetRec({ name = xt; args = yts; body = e1 }, (decide_address e2))
  | LetTuple(xts, e1, e2) -> LetTuple(xts, e1, decide_address e2)
  | ExprWithPos(e, p) -> ExprWithPos(decide_address e, p)
  | e -> e

let rec mem x yts = (* composeの補助関数 *)
  match yts with
  | [] -> false
  | (y,t) :: res -> if y = x then true else (mem x res)
(* lisに入っている(x,e,t)をexpにくっつけていく。ただし、関数の引数の名前がグローバル変数に被った場合は、グローバル変数のアドレスを挿入しない（関数内ではグローバル変数よりも引数の方がスコープが狭いので優先） *)
let rec compose exp lis yts = 
  match lis with
  | [] -> exp
  | (x,e,t) :: res -> if (mem x yts) then (compose exp res yts) else compose (Let((x, Type.Array(t)), e, exp)) res yts

(* preletsをLetRecに入れていく *)
let rec insert_prelets exp =
  match exp with
  | LetRec({ name = xt; args = yts; body = e1 }, e2) -> LetRec({ name = xt; args = yts; body = (compose e1 !prelets yts)}, insert_prelets e2)
  | Let(xt, e1, e2) -> Let(xt, e1, (insert_prelets e2))
  | LetTuple(xts, e1, e2) -> LetTuple(xts, e1, insert_prelets e2)
  | ExprWithPos(e, p) -> ExprWithPos(insert_prelets e, p)
  | e -> e

let rec f exp =
  let exp' = decide_address exp in
  let exp'' = compose (insert_prelets exp') !prelets [] in
  (!hp, exp'')
