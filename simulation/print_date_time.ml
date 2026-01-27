
open Netlist_ast

(* Définition des chiffres en 7 segments (5 lignes x 4 colonnes) *)
let segments = [|
  [| "####"; "#  #"; "#  #"; "#  #"; "####" |]; (* 0 *)
  [| "   #"; "   #"; "   #"; "   #"; "   #" |]; (* 1 *)
  [| "####"; "   #"; "####"; "#   "; "####" |]; (* 2 *)
  [| "####"; "   #"; "####"; "   #"; "####" |]; (* 3 *)
  [| "#  #"; "#  #"; "####"; "   #"; "   #" |]; (* 4 *)
  [| "####"; "#   "; "####"; "   #"; "####" |]; (* 5 *)
  [| "####"; "#   "; "####"; "#  #"; "####" |]; (* 6 *)
  [| "####"; "   #"; "   #"; "   #"; "   #" |]; (* 7 *)
  [| "####"; "#  #"; "####"; "#  #"; "####" |]; (* 8 *)
  [| "####"; "#  #"; "####"; "   #"; "####" |]; (* 9 *)
|]

(* Séparateurs *)
let separator_dots = [| "    "; " ## "; "    "; " ## "; "    " |]
(* Slash corrigé pour aller tout en bas *)
let separator_slash = [| "    #"; "   # "; "  #  "; " #   "; "#    " |]

(* Conversion jour de l'année (1-365) -> (jour, mois) pour 2026 *)
let get_date_from_day_of_year doy =
  let days_in_months = [31; 28; 31; 30; 31; 30; 31; 31; 30; 31; 30; 31] in
  let rec find_month d m_list current_month =
    match m_list with
    | [] -> (d, current_month)
    | h :: t ->
        if d <= h then (d, current_month)
        else find_month (d - h) t (current_month + 1)
  in
  find_month doy days_in_months 1

let to_digits n =
  if n < 10 then [0; n]
  else if n < 100 then [n / 10; n mod 10]
  else 
    let s = string_of_int n in
    List.init (String.length s) (fun i -> int_of_char s.[i] - int_of_char '0')

(* Fonction d'impression avec espace réduit (un seul espace entre les chiffres) *)
let print_row components row_idx =
  List.iter (fun comp ->
    match comp with
    | `Digit n -> print_string (segments.(n).(row_idx) ^ " ")
    | `TimeSep -> print_string (separator_dots.(row_idx) ^ " ")
    | `DateSep -> print_string (separator_slash.(row_idx) ^ " ")
  ) components;
  print_newline ()

let display_clock sec min hour doy year =
  let (day_of_month, month) = get_date_from_day_of_year doy in
  
  let time_line = 
    List.map (fun d -> `Digit d) (to_digits hour) @ [`TimeSep] @
    List.map (fun d -> `Digit d) (to_digits min) @ [`TimeSep] @
    List.map (fun d -> `Digit d) (to_digits sec) 
  in
  let date_line = 
    List.map (fun d -> `Digit d) (to_digits day_of_month) @ [`DateSep] @
    List.map (fun d -> `Digit d) (to_digits month) @ [`DateSep] @
    List.map (fun d -> `Digit d) (to_digits year)
  in

  print_endline "================== HEURE ==================";
  for i = 0 to 4 do print_row time_line i done;
  
  print_endline "\n================== DATE ===================";
  for i = 0 to 4 do print_row date_line i done;
  print_string "\n"

let bits_to_int = function VBit _ -> failwith "bad output"
    | VBitArray a ->
    let n = Array.length a in
    let m = min n 13 in
    let s = ref 0 in
    for i = 0 to m-1 do
        s := (!s lsl 1) + (if a.(m-1-i) then 1 else 0)
    done;
    !s

let bits_to_str bits = Int.to_string (bits_to_int bits)

let fixed_length_str len str =
    let s = ref str in
    while String.length !s < len do
        s := " " ^ !s
    done; !s

let print_date_time step env =
    let k = 3 in
    let list = [
        ("secondes", "sec");
        ("minutes", "min");
        ("heures", "h");
        ("jours", "day");
        ("mois", "month");
        ("annees", "year");
        ("clock", "clock");
        ("time", "time")
    ] in
    let print_elt (id, label) =
        try (
            let str = Env.find id env
                |> bits_to_str
                |> fixed_length_str k
            in Format.printf "%s : %s | " label str
        ) with Not_found ->
            failwith (id ^ " is not an output")
    in
    Format.printf "Step %s | " (fixed_length_str 7 (Int.to_string step));
    List.iter print_elt list;
    Format.printf "@.";
    let sec = bits_to_int (Env.find "secondes" env) in
    let min = bits_to_int (Env.find "minutes" env) in
    let heure = bits_to_int (Env.find "heures" env) in
    let jour = bits_to_int (Env.find "jours" env) in
    let annee = bits_to_int (Env.find "annees" env) in
    display_clock sec min heure jour annee
    


