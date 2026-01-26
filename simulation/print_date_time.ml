
open Netlist_ast

let bits_to_str = function VBit _ -> failwith "bad output"
    | VBitArray a ->
    let n = Array.length a in
    let m = min n 13 in
    let s = ref 0 in
    for i = 0 to m-1 do
        s := (!s lsl 1) + (if a.(m-1-i) then 1 else 0)
    done;
    Int.to_string !s


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
        ("annees", "year");
        ("mois", "month")
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
    Format.printf "@."


