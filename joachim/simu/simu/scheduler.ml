open Netlist_ast
open Graph

exception Combinational_cycle

let read_exp eq =
  let (out_var, expression) = eq in
  let args = ref [] in
  let process_arg = function
    | Avar x -> args := x::(!args)
    | _ -> () in
  (match expression with
    | Earg a -> process_arg a
    | Enot a -> process_arg a
    | Ebinop (_, a1, a2) -> process_arg a1; process_arg a2
    | Emux (a1, a2, a3) -> process_arg a1; process_arg a2; process_arg a3
    | Erom (_, _, a) -> process_arg a
    | Eram (_, _, a1, a2, a3, a4) -> process_arg a1(*; process_arg a2; process_arg a3; process_arg a4*)
    | Econcat (a1, a2) -> process_arg a1; process_arg a2
    | Eslice (_, _, a) -> process_arg a
    | Eselect (_, a) -> process_arg a
    | _ -> ());
  !args


let schedule p =
  let g = mk_graph () in
  let treat_line eq =
    let affected_var, _ = eq in
    let input_vars = read_exp eq in
    List.iter (fun x ->
      try
        ignore (node_of_label g x)
      with
        | Not_found -> add_node g x) (affected_var::input_vars);
    List.iter (fun x -> add_edge g x affected_var) input_vars in
  List.iter treat_line p.p_eqs;
  (*TEST REGISTRES*)
  List.iter (fun x -> match x with
    | (affected_var, Ereg origin_var) -> add_edge g affected_var origin_var 
    | _ -> ()) p.p_eqs;
  (*--------------*)
  (*Exercise 6*)
  Printf.printf "Length of the critical path = %d\n" (critical_path g);
  (*----------*)
  try
    let topo_order = topological g in
    let sorted_instructions = List.rev
      (List.fold_left (fun acc x -> (List.filter (fun (affected_var, _) -> x = affected_var) p.p_eqs)@acc) [] topo_order) in
    {
      p_eqs = sorted_instructions;
      p_inputs = p.p_inputs;
      p_outputs = p.p_outputs;
      p_vars = p.p_vars;
    }
  with
    | Cycle -> raise Combinational_cycle
  

(*Exercise 6*)
let delay_ident p id =
  let len_max = List.fold_left (fun acc str -> max acc (String.length (fst str))) 0 (Env.bindings p.p_vars) in
  let new_id = id ^ (String.init (min 0 (len_max + 1 - 4 - (String.length id))) (fun _ -> '_')) ^ "_reg" in
  let rec good_insert = function
    | (str, instr)::r when str = id -> (new_id, instr)::(id, Ereg new_id)::r
    | h::t -> h::(good_insert t) 
    | _ -> failwith "id not in program" in
  {
    p_eqs = good_insert p.p_eqs; (* equations *)
    p_inputs = p.p_inputs; (* inputs *)
    p_outputs = p.p_outputs; (* outputs *)
    p_vars = Env.add new_id (Env.find id p.p_vars) p.p_vars
  }