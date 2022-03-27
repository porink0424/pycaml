type t = (* MinCamlの型を表現するデータ型 (caml2html: type_t) *)
  | Unit
  | Bool
  | Int
  | Float
  | Fun of t list * t (* arguments are uncurried *)
  | Tuple of t list
  | Array of t
  | Var of t option ref

let gentyp () = Var(ref None) (* 新しい型変数を作る *)

(* print functions *)
let rec print_type t =
  match t with
  | Unit -> print_string "()"
  | Bool -> print_string "bool"
  | Int -> print_string "int"
  | Float -> print_string "float"
  | Fun (a,b) ->
      (print_string "Fun(";
       print_type_list a false;
       print_string ", ";
       print_type b;
       print_string ")")
  | Tuple a ->
      (print_string "Tuple(";
       print_type_list a false;
       print_string ")")
  | Array a -> 
      (print_string "Array(";
       print_type a;
       print_string ")")
  | Var a ->
      (print_string "Var(";
       match !a with
       | None -> print_string ")"
       | Some b -> (print_type b; print_string ")"))
and print_type_list l flg = 
       match l with
       | [] -> print_string "]"
       | x::rest -> 
         (if flg then print_string "; " else print_string "["; (* １つ目なら"["，２つ目以降なら";"を表示 *)
          print_type x;
          print_type_list rest true)

let rec type2string t = 
 match t with
  | Unit -> "()"
  | Bool -> "bool"
  | Int -> "int"
  | Float -> "float"
  | Fun (a,b) ->
        "Fun(" 
        ^ (type_list2string a false)
        ^ ","
        ^ (type2string b)
        ^ ")"
  | Tuple a ->
       "Tuple("
       ^ (type_list2string a false)
       ^ ")"
  | Array a -> 
       "Array("
       ^ (type2string a)
       ^ ")"
  | Var a -> 
      "Var("
      ^ (match !a with
       | None ->  ")"
       | Some b -> (type2string b ^ ")"))
and type_list2string l flg = 
       match l with
       | [] ->  "]"
       | x::rest -> 
         ((if flg then  ";" else  "[") (* １つ目なら"["，２つ目以降なら";"を表示 *)
          ^ (type2string x)
          ^ (type_list2string rest true))