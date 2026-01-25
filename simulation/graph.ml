exception Cycle
type mark = NotVisited | InProgress | Visited

type 'a graph =
    { mutable g_nodes : 'a node list }
and 'a node = {
  n_label : 'a;
  mutable n_mark : mark;
  mutable n_link_to : 'a node list;
  mutable n_linked_by : 'a node list;
}

let mk_graph () = { g_nodes = [] }

let add_node g x =
  let n = { n_label = x; n_mark = NotVisited; n_link_to = []; n_linked_by = [] } in
  g.g_nodes <- n :: g.g_nodes

let node_of_label g x =
  List.find (fun n -> n.n_label = x) g.g_nodes

let add_edge g id1 id2 =
  try
    let n1 = node_of_label g id1 in
    let n2 = node_of_label g id2 in
    n1.n_link_to   <- n2 :: n1.n_link_to;
    n2.n_linked_by <- n1 :: n2.n_linked_by
  with Not_found -> Format.eprintf "Tried to add an edge between non-existing nodes"; raise Not_found

let clear_marks g =
  List.iter (fun n -> n.n_mark <- NotVisited) g.g_nodes

let find_roots g =
  List.filter (fun n -> n.n_linked_by = []) g.g_nodes

let has_cycle g =
  clear_marks g;
  let rec explore node =
    if node.n_mark = Visited then false
    else if node.n_mark = InProgress then true
    else begin
      node.n_mark <- InProgress;
      let res = List.exists explore node.n_link_to in
      node.n_mark <- Visited;
      res
    end in
  List.exists explore g.g_nodes

let topological g = if has_cycle g then raise Cycle else
  let res = ref [] in
  clear_marks g;
  let rec explore node =
    if node.n_mark <> NotVisited then () else
      begin
        node.n_mark <- Visited;
        List.iter explore node.n_link_to;
        res := (node.n_label)::(!res)
      end in
  List.iter explore g.g_nodes;
  !res

(*Lab session 3 : exercise 6*)
module IndxNode = struct
  include Map.Make(struct
    type t = string
    let compare = compare
  end)
end


let critical_path g = if has_cycle g then raise Cycle else
  let lengths = ref IndxNode.empty in
  List.iter (fun n -> lengths := IndxNode.add n.n_label (-1) !lengths) g.g_nodes;
  let rec explore n = match IndxNode.find n.n_label !lengths with
    | -1 ->
      lengths := IndxNode.add n.n_label (List.fold_left (fun acc m -> max acc (explore m + 1)) 0 n.n_link_to) !lengths;
      explore n
    | i -> i in
  List.fold_left (fun acc m -> max acc (explore m)) 0 g.g_nodes
