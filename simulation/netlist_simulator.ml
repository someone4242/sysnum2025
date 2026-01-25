open Netlist_ast

let print_only = ref false
let number_steps = ref (-1)
let rom_file_name = ref ""

exception SimulationError
exception RomConfigurationError of string


let unpack_roms filename roms_specs = 
  let ic = Netlist.find_file filename in

  let read_a_rom id =
    let list_of_content = ref [] in
    let read_content () =
    try
      let line = ref (input_line ic) in
      while (String.length !line > 0) do
        list_of_content := !line::(!list_of_content);
        line := input_line ic
      done;
    with
      | End_of_file -> () in
    read_content ();
    if (Env.mem id roms_specs) then
    (
      let (addr_size, word_size) = Env.find id roms_specs in
      Array.map (fun str ->
          if String.exists (fun x -> x <> '0' && x <> '1') str then
            raise (RomConfigurationError ("Rom " ^ id ^ " contains unallowed characters"));
          if (String.length str <> word_size) then
            raise (RomConfigurationError ("Rom " ^ id ^ " contains words of incorrect size"));
          VBitArray (Array.init word_size (fun i -> if str.[i] = '0' then false else true)))
        (Array.of_list (List.rev !list_of_content))
    )
    else [||]
    in
    

  let rec build_roms () = 
    try
      let id = input_line ic in
      let cnt = read_a_rom id in
      Env.add id cnt (build_roms ())
    with
      | End_of_file -> Env.empty in

  build_roms ()

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
  let rams = ref Env.empty in
  let ram_init_instr (id, ep) = match ep with
    | Eram (addr_size, word_size, _, _, _, _) ->
      let size = word_size*(1 lsl addr_size) in
      rams := Env.add id (Array.make size false) (!rams) (*ram is represented by a continuous array of bits*)
    | _ -> () in
  List.iter ram_init_instr program.p_eqs;

  let roms_specs = ref Env.empty in
  let rom_spec_init (id, ep) = match ep with
    | Erom (addr_size, word_size, _) ->
      roms_specs := Env.add id (addr_size, word_size) !roms_specs
    | _ -> () in
  List.iter rom_spec_init program.p_eqs;
  let roms = if String.length !rom_file_name > 0 
    then (unpack_roms !rom_file_name !roms_specs)
    else Env.empty
  in

  let future_write = ref [] in
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

  let rec nlbinop_aux op a1 a2 = match (a1, a2) with
    | (VBit t1, VBit t2) -> VBit (op t1 t2)
    | (VBitArray arr1, VBitArray arr2) when Array.length arr1 = Array.length arr2 ->
      VBitArray (Array.map2 op arr1 arr2)
    | (VBit t, VBitArray arr) when Array.length arr = 1 ->
      nlbinop_aux op (VBit t) (VBit arr.(0))
    | (VBitArray arr, VBit t) when Array.length arr = 1 -> 
      nlbinop_aux op (VBit arr.(0)) (VBit t)
    | _ -> assert false in

  let nlbinop a1 a2 = function
    | Xor -> nlbinop_aux (fun t1 t2 -> (t1 && (not t2)) || (t2 && (not t1))) a1 a2
    | Or -> nlbinop_aux (||) a1 a2
    | Nand -> nlbinop_aux (fun t1 t2 -> not (t1 && t2)) a1 a2
    | And -> nlbinop_aux (&&) a1 a2 in

  let nlmux m a1 a2 = match m with
    | VBit true -> a2
    | VBit false -> a1
    | _ -> assert false in
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
    | _ -> assert false in

  let nlselect i = function
    | VBitArray arr when i < Array.length arr -> VBit arr.(i)
    | _ -> assert false in

  let unpack_data = function
    | VBitArray arr -> arr
    | _ -> assert false in

  let bit_arrays_to_int = function
    | VBit x -> if x then 1 else 0
    | VBitArray arr -> Array.fold_right (fun a acc -> 2*acc + (if a then 1 else 0)) arr 0
  in 
  let nlram id word_size read_addr write_enable write_addr data = match write_enable with
    | VBit false -> (*lecture*)
      VBitArray (Array.sub (Env.find id !rams) (read_addr*word_size) word_size)
    | VBit true -> (*écriture*)
      future_write := ((id, word_size, write_addr, data))::(!future_write);
      VBitArray (Array.sub (Env.find id !rams) (read_addr*word_size) word_size)
    | _ -> assert false in

  (*Processing the write instruction after the cycle*)
  let update_rams_cycle () =
    while !future_write <> [] do
      let id, word_size, write_addr, data = List.hd !future_write in
      future_write := List.tl !future_write;
      let arr = Env.find id !rams in
      let pos = bit_arrays_to_int (read_arg write_addr) in
      Array.iteri (fun i bit -> arr.((pos)*word_size + i) <- bit) (unpack_data (read_arg data));
    done in
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
      if (Env.mem assigned_var roms) then
        let arr = Env.find assigned_var roms in
        let addr = bit_arrays_to_int (read_arg a) in
        if (Array.length arr > addr) then
          env := Env.add assigned_var arr.(addr) (!env)

      (* Rom remplie de zéros dans les cas non spécifiés*)
        else
          env := Env.add assigned_var (VBitArray (Array.make word_size false)) (!env)
        else
      env := Env.add assigned_var (VBitArray (Array.make word_size false)) (!env)
    | Eram (addr_size, word_size, read_addr, write_enable, write_addr, data) ->
      let res = nlram assigned_var word_size
        (bit_arrays_to_int (read_arg read_addr)) (read_arg write_enable)
        write_addr data in
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
    [("-n", Arg.Set_int number_steps, "Number of steps to simulate");
    ("-rom", Arg.Set_string rom_file_name, "Name of the ROM file")]
    compile
    ""
;;

main ()
