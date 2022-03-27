(* minrtを動かすために必要な組み込み関数 *)
(* mincamlで書いた上でコンパイラを使ってそれをアセンブリに起こして、それをminrt.sの先頭に加えることで組み込み関数として対応する *)

(* xを0~2piの間の値にする *)
let rec simplify x =
  if x >= 6.28318530718 then (simplify (x -. 6.28318530718))
  else (if x < 0.0 then (simplify (x +. 6.28318530718))
  else x)
in

(* 0~pi/4の間のsinを計算する *)
let rec narrow_range_sin x =
  let x2 = x *. x in
  let x3 = x2 *. x in
  let x5 = x3 *. x2 in
  let x7 = x5 *. x2 in
  (x -. (x3 *. 0.1666666666) +. (x5 *. 0.0083333333) -. (x7 *. 0.00019841269))
in

(* 0~pi/4の間のcosを計算する *)
let rec narrow_range_cos x =
  let x2 = x *. x in
  let x4 = x2 *. x2 in
  let x6 = x4 *. x2 in
  (1.0 -. (x2 *. 0.5) +. (x4 *. 0.04166666666) -. (x6 *. 0.00138888888))
in

let rec sin x =
  let simplified_x = (simplify x) in
  if simplified_x <= 0.78539816339 then (narrow_range_sin simplified_x) (* 0~pi/4 *)
  else if simplified_x <= 1.57079632679 then (narrow_range_cos (1.57079632679 -. simplified_x)) (* pi/4~pi/2 *)
  else if simplified_x <= 3.1415926535 then (sin (3.1415926535 -. simplified_x)) (* pi/2~pi *)
  else if simplified_x <= 4.71238898038 then (-.(sin (simplified_x -. 3.1415926535))) (* pi~3pi/2 *)
  else (-.(sin (6.28318530718 -. simplified_x))) (* 3pi/2~2pi *)
in

let rec cos x =
  (sin (1.57079632679 +. x))
in

(* 0~√2-1の間のatanを計算する *)
let rec narrow_range_atan x =
  let x2 = x *. x in
  let x3 = x2 *. x in
  let x5 = x3 *. x2 in
  let x7 = x5 *. x2 in
  let x9 = x7 *. x2 in
  let x11 = x9 *. x2 in
  (x -. (x3 *. 0.33333333333) +. (x5 *. 0.2) -. (x7 *. 0.14285714285) +. (x9 *. 0.11111111111) -. (x11 *. 0.0909090909))
in

let rec atan x =
  if x >= 0.0 then
    if x < 0.41421356237 then (narrow_range_atan x) (* 0 ~ √2-1 *)
    else if x <= 1.0 then (0.78539816339 -. (narrow_range_atan ((1.0 -. x) /. (1.0 +. x)))) (* √2-1 ~ 1 *)
    else (1.57079632679 -. (atan (1.0 /. x))) (* 1 ~ *)
  else -.(atan (-.x)) (* ~ 0 *)
in
