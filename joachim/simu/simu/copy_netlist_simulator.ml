open Netlist_ast

let print_only = ref false
let number_steps = ref (-1)

exception SimulationError

let simulator program number_steps =
  (*Initialisation of the environment*)
  let env = ref Env.empty in
  List.iter (fun (k, t) -> match t with
    | TBit -> env := Env.add k (VBit false) (!env)
    | TBitArray n -> env := Env.add k (VBitArray (Array.make n false)) (!env)
  ) (Env.bindings program.p_vars);
  (*---------------------------------*)

  (*Initialisation RAM/ROM/Registers*)
  let registers = ref (!env) in
  let rams = ref Env.empty in (*Paires lecture/écriture*)
  let ram_init_instr (id, ep) = match ep with
    | Eram (addr_size, word_size, _, _, _, _) ->
      let size = word_size*(1 lsl addr_size) in
      rams := Env.add id (Array.make size false, Array.make size false) (!rams)
    | _ -> () in
  List.iter ram_init_instr program.p_eqs;

  let update_rams_cycle () =
    let update_one_ram (id, (rd, wt)) =
      rams := Env.add id (wt, Array.copy wt) !rams in
    List.iter update_one_ram (Env.bindings !rams) in

  (*--------------------------------*)

  (*Function to parse the input given by the user*)
  let parse_input id =
    let is_correct_parsing ip =
      let char_lst = String.fold_right (fun c acc -> c::acc) ip [] in
      if (List.exists (fun x -> (x <> '0' && x <> '1')) char_lst) then None
      else match (Env.find id program.p_vars) with
        | TBit when String.length ip = 1 -> Some (VBit (ip.[0] = '1'))
        | TBitArray n when n = String.length ip -> 
          Some (VBitArray (Array.init n (fun i -> ip.[i] = '1')))
        | _ -> None in
    Printf.printf "%s = " id;
    let user_input = ref (read_line ()) in
    let call = ref (is_correct_parsing !user_input) in
    while (!call = None) do
      Printf.printf "Incorrect input :( I am very sad :( :( :(\n%s = " id;
      user_input := read_line ();
      call := is_correct_parsing !user_input
    done;
    (*Printf.printf "\n";*)
    env := Env.add id (Option.get !call) (!env) in
  (*---------------------------------------------*)

  (*Function to print the outputs*)
  let print_output id =
    let value_to_str = function
      | VBit t -> if t then "1" else "0"
      | VBitArray arr -> 
        String.concat "" (List.map (fun t -> if t then "1" else "0") (Array.to_list arr))
    in
    Printf.printf "%s = %s\n" id (value_to_str (Env.find id (!env))) in
  (*-----------------------------*)

  (*Function to get the value of an argument*)
  let read_arg = function
    | Aconst x -> x
    | Avar v -> Env.find v (!env) in
  (*----------------------------------------*)

  (*Logical functions*)
  let nlnot = function
    | VBit t -> VBit (not t)
    | VBitArray arr -> VBitArray (Array.map not arr) in

  let nlbinop_aux op a1 a2 = match (a1, a2) with
    | (VBit t1, VBit t2) -> VBit (op t1 t2)
    | (VBitArray arr1, VBitArray arr2) when Array.length arr1 = Array.length arr2 ->
      VBitArray (Array.map2 op arr1 arr2)
    | _ -> raise SimulationError in

  let nlbinop a1 a2 = function
    | Xor -> nlbinop_aux (fun t1 t2 -> (t1 && (not t2)) || (t2 && (not t1))) a1 a2
    | Or -> nlbinop_aux (||) a1 a2
    | Nand -> nlbinop_aux (fun t1 t2 -> not (t1 && t2)) a1 a2
    | And -> nlbinop_aux (&&) a1 a2 in

  let nlmux m a1 a2 = match m with
    | VBit true -> a2
    | VBit false -> a1
    | _ -> raise SimulationError in
  (*-----------------*)

  (*Misc function for other operations*)
  let nlconcat a1 a2 = match (a1, a2) with
    | (VBit t1, VBit t2) -> VBitArray [|t1; t2|]
    | (VBit t1, VBitArray arr2) -> VBitArray (Array.append [|t1|] arr2)
    | (VBitArray arr1, VBit t2) -> VBitArray (Array.append arr1 [|t2|])
    | (VBitArray arr1, VBitArray arr2) ->
      VBitArray (Array.append arr1 arr2) in

  let nlslice i1 i2 = function
    | VBitArray arr when i2 < i1 -> VBitArray (Array.make 0 false)
    | VBitArray arr when i2 < Array.length arr -> 
      VBitArray (Array.sub arr i1 (i2 - i1 + 1)) 
    | _ -> raise SimulationError in

  let nlselect i = function
    | VBitArray arr when i < Array.length arr -> VBit arr.(i)
    | _ -> raise SimulationError in

  let unpack_data = function
    | VBitArray arr -> arr
    | _ -> raise SimulationError in

  let bit_arrays_to_int = function
    | VBitArray arr -> Array.fold_right (fun a acc -> 2*acc + (if a then 1 else 0)) arr 0
    | _ -> raise SimulationError in

  let nlram id word_size read_addr write_enable write_addr data = match write_enable with
    | VBit false -> (*lecture*)
      VBitArray (Array.sub (fst (Env.find id !rams)) (read_addr*word_size) word_size)
    | VBit true -> (*écriture*)
      let _, arr = Env.find id !rams in
      Array.iteri (fun i bit -> arr.(read_addr*word_size + i) <- bit) (unpack_data data);
      data
    | _ -> raise SimulationError in
  (*----------------------------------*)

  (*Function to execute an instruction*)
  let assign_var (assigned_var, ep) = match ep with
    | Earg a -> env := Env.add assigned_var (read_arg a) (!env)
    | Ereg id -> env := Env.add assigned_var (Env.find id (!registers)) (!env)
    | Enot a -> env := Env.add assigned_var (nlnot (read_arg a)) (!env)
    | Ebinop (op, a1, a2) ->
      env := Env.add assigned_var (nlbinop (read_arg a1) (read_arg a2) op) (!env)
    | Emux (m, a1, a2) ->
      env := Env.add assigned_var (nlmux (read_arg m) (read_arg a1) (read_arg a2)) (!env)
    | Erom (addr_size, word_size, a) ->
      (* Rom remplie de zéros *)
      env := Env.add assigned_var (VBitArray (Array.make word_size false)) (!env)
    | Eram (addr_size, word_size, read_addr, write_enable, write_addr, data) ->
      let res = nlram assigned_var word_size
        (bit_arrays_to_int (read_arg read_addr)) (read_arg write_enable)
        (bit_arrays_to_int (read_arg write_addr)) (read_arg data) in
      env := Env.add assigned_var res !env
    | Econcat (a1, a2) ->
      env := Env.add assigned_var (nlconcat (read_arg a1) (read_arg a2)) (!env)
    | Eslice (i1, i2, a) ->
      env := Env.add assigned_var (nlslice i1 i2 (read_arg a)) (!env)
    | Eselect (i, a) ->
      env := Env.add assigned_var (nlselect i (read_arg a)) (!env) in
  (*----------------------------------*)

  (*Do a step*)
  let do_a_step () =
    (*Inputs*)
    List.iter parse_input program.p_inputs;
    (*Instructions*)
    List.iter assign_var program.p_eqs;
    (*Outputs*)
    List.iter print_output program.p_outputs;
    (*Save registers, update ram*)
    registers := !env;
    update_rams_cycle ()
  in

  (*Simulation of the steps*)
  if (number_steps >= 0) then
  begin
    for step_i = 1 to number_steps do
      Printf.printf "Step %d:\n" step_i;
      do_a_step ();
    done
  end
  else
  begin
    let step = ref 1 in
    while (0 <> 42) do
      Printf.printf "Step %d:\n" !step;
      do_a_step ();
      incr step;
    done
  end

let compile filename =
  try
    let p = Netlist.read_file filename in
    begin try
        let p = Scheduler.schedule p in
        simulator p !number_steps
      with
        | Scheduler.Combinational_cycle ->
            Format.eprintf "The netlist has a combinatory cycle.@.";
    end;
  with
    | Netlist.Parse_error s -> Format.eprintf "An error accurred: %s@." s; exit 2

let main () =
  Arg.parse
    ["-n", Arg.Set_int number_steps, "Number of steps to simulate"]
    compile
    ""
;;

main ()
