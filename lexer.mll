{
(* lexer�����Ѥ����ѿ����ؿ������ʤɤ���� *)
open Parser
open Type
}

(* ����ɽ����ά�� *)
let space = [' ' '\t' '\r']
let newline = ['\n']
let digit = ['0'-'9']
let lower = ['a'-'z']
let upper = ['A'-'Z']

rule token = parse
| space+
    { token lexbuf }
| newline 
    { Lexing.new_line lexbuf;
      token lexbuf }
| "(*"
    { comment lexbuf; (* �ͥ��Ȥ��������ȤΤ���Υȥ�å� *)
      token lexbuf }
| '('
    { LPAREN }
| ')'
    { RPAREN }
| "true"
    { BOOL(true) }
| "false"
    { BOOL(false) }
| "not"
    { NOT }
| "fun"
    { FUN }
| digit+ (* �����������Ϥ���롼�� (caml2html: lexer_int) *)
    { INT(int_of_string (Lexing.lexeme lexbuf)) }
| digit+ ('.' digit*)? (['e' 'E'] ['+' '-']? digit+)?
    { FLOAT(float_of_string (Lexing.lexeme lexbuf)) }
| '-' (* -.����󤷤ˤ��ʤ��Ƥ��ɤ�? ��Ĺ����? *)
    { MINUS }
| '+' (* +.����󤷤ˤ��ʤ��Ƥ��ɤ�? ��Ĺ����? *)
    { PLUS }
| '*'
    { AST }
| '/'
    { SLASH }
| "-."
    { MINUS_DOT }
| "+."
    { PLUS_DOT }
| "*."
    { AST_DOT }
| "/."
    { SLASH_DOT }
| '='
    { EQUAL }
| "<>"
    { LESS_GREATER }
| "<="
    { LESS_EQUAL }
| ">="
    { GREATER_EQUAL }
| '<'
    { LESS }
| '>'
    { GREATER }
| "if"
    { IF }
| "then"
    { THEN }
| "else"
    { ELSE }
| "let"
    { LET }
| "in"
    { IN }
| "rec"
    { REC }
| "global"
    { GLOBAL }
| ','
    { COMMA }
| '_'
    { IDENT(Id.gentmp Type.Unit) }
| "Array.create" | "Array.make" (* [XX] ad hoc *)
    { ARRAY_CREATE }
| '.'
    { DOT }
| "<-"
    { LESS_MINUS }
| "->"
    { MINUS_GREATER }
| ';'
    { SEMICOLON }
| eof
    { EOF }
| lower (digit|lower|upper|'_')* (* ¾�Ρ�ͽ���פ���Ǥʤ��Ȥ����ʤ� *)
    { IDENT(Lexing.lexeme lexbuf) }
| _
    { 
      let curr = lexbuf.Lexing.lex_curr_p in
      let line = curr.Lexing.pos_lnum in
      let offset = curr.Lexing.pos_cnum - curr.Lexing.pos_bol in 
      failwith
        (Printf.sprintf "unknown token %s near characters %d-%d, line %d, offset %d"
           (Lexing.lexeme lexbuf)
           (Lexing.lexeme_start lexbuf)
           (Lexing.lexeme_end lexbuf)
           line 
           offset) }
and comment = parse
| "*)"
    { () }
| "(*"
    { comment lexbuf;
      comment lexbuf }
| newline 
    { Lexing.new_line lexbuf;
      comment lexbuf }
| eof
    { Format.eprintf "warning: unterminated comment@." }
| _
    { comment lexbuf }
